import asyncio
import time
import botpy
from botpy import BotAPI
from botpy.ext.command_util import Commands
from botpy.manage import GroupManageEvent
from botpy.message import Message, DirectMessage, GroupMessage, BaseMessage
import aiohttp

import r

_log = botpy.logging.get_logger()

session: aiohttp.ClientSession


@Commands("查电费")
async def query_electricity_balance(message: GroupMessage, params=None):
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

            uploadMedia = await message._api.post_group_file(
                group_openid=message.group_openid,
                file_type=1,
                url= image_url
            )

            reply_content = (
                f"\n"
                f"服务器名称: SIT-Minecraft\n"
                f"描述: {description}\n"
                f"在线玩家: {players_online}/{players_max}\n"
                f"版本: {version}\n"
                f"查询时间: {timestamp}"
            )

            await message._api.post_group_message(
                content=reply_content,
                group_openid=message.group_openid,
                msg_type=7,
                msg_id=message.id,
                media=uploadMedia
            )
            return True
        else:
            error_content = (
                f"查询SITMC服务器信息失败\n"
                f"状态码: {res.status}\n"
                f"响应内容: {result}"
            )
            await message.reply(content=error_content)
            return True


@Commands("查天气")
async def query_weather(api: BotAPI, message: GroupMessage, params=None):
    async with aiohttp.ClientSession() as session:
        fx_res, xh_res = await asyncio.gather(
            session.get(f"https://restapi.amap.com/v3/weather/weatherInfo?city=310120&key=" + r.WeatherApiToken),
            session.get(f"https://restapi.amap.com/v3/weather/weatherInfo?city=310104&key=" + r.WeatherApiToken)
        )

        if fx_res.ok:
            fx_result = await fx_res.json()
            xh_result = await xh_res.json()
            if fx_result.get("status") == "1" and "lives" in fx_result and len(fx_result["lives"]) > 0:
                fx_live_data = fx_result["lives"][0]
                xh_live_data = xh_result["lives"][0]

                fx_weather = fx_live_data.get("weather", "N/A")
                fx_temperature = fx_live_data.get("temperature", "N/A")
                fx_winddirection = fx_live_data.get("winddirection", "N/A")
                fx_windpower = fx_live_data.get("windpower", "N/A")
                fx_humidity = fx_live_data.get("humidity", "N/A")

                xh_weather = xh_live_data.get("weather", "N/A")
                xh_temperature = xh_live_data.get("temperature", "N/A")
                xh_winddirection = xh_live_data.get("winddirection", "N/A")
                xh_windpower = xh_live_data.get("windpower", "N/A")
                xh_humidity = xh_live_data.get("humidity", "N/A")

                reporttime = fx_live_data.get("reporttime", "N/A")

                reply_content = (
                    f"\n"
                    f"奉贤校区：\n"
                    f"天气：{fx_weather}\n"
                    f"温度：{fx_temperature}\n"
                    f"风向：{fx_winddirection}\n"
                    f"风力：{fx_windpower}\n"
                    f"湿度：{fx_humidity}\n"
                    f"\n"
                    f"徐汇校区：\n"
                    f"天气：{xh_weather}\n"
                    f"温度：{xh_temperature}\n"
                    f"风向：{xh_winddirection}\n"
                    f"风力：{xh_windpower}\n"
                    f"湿度：{xh_humidity}\n"
                    f"更新时间：{reporttime}"
                )

                await message.reply(content=reply_content)
            else:
                error_content = "查询失败，响应数据不正确"
                await message.reply(content=error_content)
        else:
            error_content = "查询失败，无法连接到天气服务"
            await message.reply(content=error_content)
        return True


@Commands("学校服务状态")
async def query_school_server(api: BotAPI, message: GroupMessage, params=None):
    urls = {
        "教务系统": "https://xgfy.sit.edu.cn/unifri-flow/WF/Comm/ProcessRequest.do?DoType=DBAccess_RunSQLReturnTable",
        "电费服务器": "https://myportal.sit.edu.cn/?rnd=1",
        "消费服务器": "https://xgfy.sit.edu.cn/yktapi/services/querytransservice/querytrans"
    }

    async def fetch_status(session, name, url):
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

    async def check_server_status(urls):
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_status(session, name, url) for name, url in urls.items()]
            statuses = await asyncio.gather(*tasks)

            status_dict = dict(statuses)

            reply_content = (
                f"\n"
                f"教务系统: {status_dict['教务系统']}\n"
                f"电费服务器: {status_dict['电费服务器']}\n"
                f"消费服务器: {status_dict['消费服务器']}\n"
            )

        await message.reply(content=reply_content)


@Commands("绑定")
async def bind_context(api: BotAPI, message: GroupMessage, params=None):
    pass


handlers = [
    query_electricity_balance,
    query_sitmc_server,
    query_weather,
    query_school_server,
]


class MimirClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot[{self.robot.name}] is ready.")

    async def on_group_at_message_create(self, message: GroupMessage):
        _log.info(f"Received: {message.content}")
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        await message.reply(content=message.content)

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