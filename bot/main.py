import asyncio

import botpy
from botpy import BotAPI
from botpy.ext.command_util import Commands
from botpy.manage import GroupManageEvent
from botpy.message import Message, DirectMessage, GroupMessage, BaseMessage
import aiohttp

import r
import weather

_log = botpy.logging.get_logger()

session: aiohttp.ClientSession


async def on_mimir_backend_error(message: GroupMessage):
    await message.reply(content=f"小应生活服务无响应，请稍后再试，若此问题依然存在，请联系机器人管理员")


@Commands("查电费")
async def query_electricity_balance(api: BotAPI, message: GroupMessage, params=None):
    try:
        async with session.get(f"{r.backend}/electricity/query", params={"raw": params}) as res:
            result = await res.json()
            if res.ok:
                balance = result
                await message.reply(content=f"#{balance['roomNumber']} 的电费为 {balance['balance']:.2f} 元")
            else:
                # 处理不同的错误消息
                if result.get("message") == "roomNotFound":
                    await message.reply(content="请输入正确的房间号")
                elif result.get("message") == "fetchFailed":
                    await message.reply(content=f"查询 #{result['roomNumber']} 的电费失败")
                else:
                    await message.reply(content="查询电费时出现未知错误")

    except aiohttp.ClientError as e:
        _log.error("HTTP请求失败", exc_info=True)
        await message.reply(content="无法连接到电费查询服务，请稍后再试")
    except ValueError as e:
        _log.error("解析响应失败", exc_info=True)
        await message.reply(content="解析电费查询响应时出错")
    except Exception as e:
        _log.error("查询电费时出现未知错误", exc_info=True)
        await on_mimir_backend_error(message)
    finally:
        return True


def weather4display(live: weather.WeatherLive, forcast: weather.WeatherForcast):
    cast = forcast.casts[0]

    def p(entry: weather.WeatherCastEntry):
        return f"{entry.weather} {entry.temperature}°C，{entry.wind_power}级{entry.wind_direction}风"

    return (
        f"{live.province} {live.city}：\n"
        f"{live.weather}，{live.temperature}°C，湿度{live.humidity}%，{live.wind_power}级{live.wind_direction}风\n"
        f"预测 {cast.date.month}月{cast.date.day}日：\n"
        f"白天 {p(cast.day)}\n"
        f"夜间 {p(cast.night)}"
    )


@Commands("查天气")
async def query_weather(api: BotAPI, message: GroupMessage, params=None):
    fx, xh = await asyncio.gather(
        weather.fetch(session, weather.City.feng_xian),
        weather.fetch(session, weather.City.xu_hui),
    )

    if fx is None or xh is None:
        await message.reply(content="查询失败，无法连接到天气服务")
    else:
        reply = f'\n{weather4display(*fx)}\n------------\n{weather4display(*xh)}'
        await message.reply(content=reply)
    return True


school_server_urls = {
    "教务系统": "https://xgfy.sit.edu.cn/unifri-flow/WF/Comm/ProcessRequest.do?DoType=DBAccess_RunSQLReturnTable",
    "电费服务器": "https://myportal.sit.edu.cn/?rnd=1",
    "消费服务器": "https://xgfy.sit.edu.cn/yktapi/services/querytransservice/querytrans"
}


@Commands("服务状态")
async def query_school_server(api: BotAPI, message: GroupMessage, params=None):
    async def fetch_status(name, url):
        try:
            async with session.get(url, timeout=8) as response:
                if response.status == 200:
                    return name, "正常运行"
                else:
                    return name, "连接超时"
        except asyncio.TimeoutError:
            return name, "连接超时"
        except aiohttp.ClientError:
            return name, "连接超时"

    tasks = [fetch_status(name, url) for name, url in school_server_urls.items()]
    statuses = await asyncio.gather(*tasks)

    status_dict = dict(statuses)

    reply_content = (
        f"\n"
        f"教务系统: {status_dict['教务系统']}\n"
        f"电费服务器: {status_dict['电费服务器']}\n"
        f"消费服务器: {status_dict['消费服务器']}"
    )

    await message.reply(content=reply_content)
    return True


@Commands("下载地址")
async def download_address(api: BotAPI, message: GroupMessage, params=None):
    qrcode_media = await api.post_group_file(
        group_openid=message.group_openid,
        file_type=1,
        url="https://g.mysit.life/static/img/qrcode.png"
    )
    content = "扫描二维码进入下载页。iOS用户可在App Store搜索小应生活。"
    await message.reply(
        content=content,
        msg_type=7,
        media=qrcode_media,
    )
    return True


handlers = [
    query_electricity_balance,
    query_weather,
    query_school_server,
    download_address,
]


class MimirClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot[{self.robot.name}] is ready.")

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(f"Received: {message.content}")
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        await message.reply(content=f'echo "{message.content}"')

    async def on_group_add_robot(self, message: GroupManageEvent):
        await self.api.post_group_message(group_openid=message.group_openid, content="我进群了，哥")

    async def on_group_del_robot(self, event: GroupManageEvent):
        _log.info(f"robot[{self.robot.name}] left group ${event.group_openid}")


async def main():
    global session
    session = aiohttp.ClientSession()
    intents = botpy.Intents(
        public_messages=True,
        # public_guild_messages=True,
        # direct_message=True,
    )
    client = MimirClient(intents=intents, is_sandbox=True, log_level=10, timeout=30)
    await client.start(appid=r.appid, secret=r.secret)
    await session.close()


asyncio.run(main())
