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
            return True
        elif result["reason"] == "roomNotFound":
            await message.reply(content=f"请输入正确的房间号")
            return True
        elif result["reason"] == "fetchFailed":
            await message.reply(content=f"查询 #{result['roomNumber']} 的电费失败")
            return True

        return True


@Commands("查询SITMC状态")
async def query_sitmc_server(api: BotAPI, message: GroupMessage, params=None):
    async with session.post(f"https://mc.sjtu.cn/custom/serverlist/?query=" + r.MCServer) as res:
        result = await res.json()
        if res.ok:
            server_info = result
            description = server_info.get('description_raw', {}).get('extra', [{}])[0].get('text', '无描述')
            players_max = server_info.get('players', {}).get('max', '未知')
            players_online = server_info.get('players', {}).get('online', '未知')
            version = server_info.get('version', '未知')

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            reply_content = (f"\n"
                f"服务器名称: SIT-Minecraft\n"
                f"描述: {description}\n"
                f"在线玩家: {players_online}/{players_max}\n"
                f"版本: {version}\n"
                f"查询时间: {timestamp}"
            )
            await message.reply(content=reply_content)
        else:
            error_content = (
                f"查询SITMC服务器信息失败\n"
                f"状态码: {res.status}\n"
                f"响应内容: {result}"
            )
            await message.reply(content=error_content)

handlers = [
    query_electricity_balance,
    query_sitmc_server,
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
