import asyncio
import time
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


@Commands("查电费")
async def query_electricity_balance(api: BotAPI, message: GroupMessage, params=None):
    async with session.post(f"{r.backend}/electricity/query", json={
        "rawQuery": params,
    }) as res:
        result = await res.json()
        if res.ok:
            balance = result
            await message.reply(content=f"#{balance['roomNumber']} 的电费为 {balance['balance']:.2f} 元")
        elif result["reason"] == "roomNotFound":
            await message.reply(content=f"请输入正确的房间号")
        elif result["reason"] == "fetchFailed":
            await message.reply(content=f"查询 #{result['roomNumber']} 的电费失败")

        return True


@Commands("SITMC服务器")
async def query_sitmc_server(api: BotAPI, message: GroupMessage, params=None):
    async with session.post(f"https://mc.sjtu.cn/custom/serverlist/?query=play.sitmc.club") as res:
        result = await res.json()
        if res.ok:
            server_info = result
            description = server_info.get('description_raw', {}).get('extra', [{}])[0].get('text', '无描述')
            players_max = server_info.get('players', {}).get('max', '未知')
            players_online = server_info.get('players', {}).get('online', '未知')
            version = server_info.get('version', '未知')

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            image_url = "https://status.minecraftservers.org/nether/663801.png"

            uploadMedia = await api.post_group_file(
                group_openid=message.group_openid,
                file_type=1,
                url=image_url
            )

            reply_content = (
                f"\n"
                f"服务器名称: SIT-Minecraft\n"
                f"描述: {description}\n"
                f"在线玩家: {players_online}/{players_max}\n"
                f"版本: {version}\n"
                f"查询时间: {timestamp}"
            )

            await message.reply(
                content=reply_content,
                msg_type=7,
                media=uploadMedia
            )
        else:
            error_content = (
                f"查询SITMC服务器信息失败\n"
                f"状态码: {res.status}\n"
                f"响应内容: {result}"
            )
            await message.reply(content=error_content)
        return True


def weather4display(live: weather.WeatherLive, forcast: weather.WeatherForcast):
    cast = forcast.casts[0]
    return \
        f"""{live.province} {live.city}: {live.weather}, {live.temperature}°C, 湿度{live.humidity}%, {live.wind_power}级{live.wind_direction}风.
预测 {cast.date.month}月{cast.date.day}日: 白天{cast.day.temperature}°C, {cast.day.wind_power}级{cast.day.wind_direction}风; 夜间{cast.night.temperature}°C, {cast.night.wind_power}级{cast.night.wind_direction}风.
"""


@Commands("查天气")
async def query_weather(api: BotAPI, message: GroupMessage, params=None):
    fx, xh = await asyncio.gather(
        weather.fetch(session, weather.City.feng_xian),
        weather.fetch(session, weather.City.xu_hui),
    )

    if fx is None or xh is None:
        await message.reply(content="查询失败，无法连接到天气服务")
    else:
        reply = f'\n{weather4display(*fx)}------------\n{weather4display(*xh)}'
        await message.reply(content=reply)
    return True


school_server_urls = {
    "教务系统": "https://xgfy.sit.edu.cn/unifri-flow/WF/Comm/ProcessRequest.do?DoType=DBAccess_RunSQLReturnTable",
    "电费服务器": "https://myportal.sit.edu.cn/?rnd=1",
    "消费服务器": "https://xgfy.sit.edu.cn/yktapi/services/querytransservice/querytrans"
}


@Commands("学校服务状态")
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
        f"消费服务器: {status_dict['消费服务器']}\n"
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
    query_sitmc_server,
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
