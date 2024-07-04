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


@Commands("服务状态")
async def query_sitmc_server(api: BotAPI, message: GroupMessage, params=None):
    async with session.post(r.MCServerApi + r.MCServer) as res:
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
    async with session.post(r.WeatherApi + f"?key=" + r.WeatherApiToken + f"&city=310120") as res:
        result = await res.json()
        if res.ok:
            data = result
            if "lives" in data and len(data["lives"]) > 0:
                live_data = data["lives"][0]
                city = live_data.get("city", "N/A")
                weather = live_data.get("weather", "N/A")
                temperature = live_data.get("temperature", "N/A")
                winddirection = live_data.get("winddirection", "N/A")
                windpower = live_data.get("windpower", "N/A")
                humidity = live_data.get("humidity", "N/A")
                reporttime = live_data.get("reporttime", "N/A")

                reply_content = (
                    f"城市：{city}\n"
                    f"天气：{weather}\n"
                    f"温度：{temperature}\n"
                    f"风向：{winddirection}\n"
                    f"风力：{windpower}\n"
                    f"湿度：{humidity}\n"
                    f"更新时间：{reporttime}"
                )

                await message.reply(content=reply_content)
            else:
                error_content = (f"查询失败")
                await message.reply(content=error_content)
            pass


@Commands("绑定")
async def bind_context(api: BotAPI, message: GroupMessage, params=None):
    pass


handlers = [
    query_electricity_balance,
    query_sitmc_server,
    query_weather,
    bind_context,
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
