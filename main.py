import botpy
from botpy import BotAPI
from botpy.ext.command_util import Commands
from botpy.manage import GroupManageEvent
from botpy.message import Message, DirectMessage, GroupMessage, BaseMessage
import os

import electricity

_log = botpy.logging.get_logger()


@Commands("查电费")
async def query_electricity_balance(api: BotAPI, message: GroupMessage, params=None):
    room_number = electricity.extract_room_number(params)
    if room_number is None:
        await message.reply(content=f"请输入正确的房间号")
        return True
    balance = electricity.fetch(room_number)
    if balance is None:
        await message.reply(content=f"查询 #{room_number} 的电费失败")
        return True

    await message.reply(content=f"#{balance.room_number} 的电费为 {balance.balance:.2f} 元")
    return True


handlers = [
    query_electricity_balance,
]


class MimirClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot[{self.robot.name}] is ready.")

    async def on_group_at_message_create(self, message: GroupMessage):
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        await message.reply(content=message.content)

    async def on_group_add_robot(self, message: GroupManageEvent):
        await self.api.post_group_message(group_openid=message.group_openid, content="我进群了，哥")

    async def on_group_del_robot(self, event: GroupManageEvent):
        _log.info(f"robot[{self.robot.name}] left group ${event.group_openid}")


intents = botpy.Intents(
    public_messages=True,
    # public_guild_messages=True,
    # direct_message=True,
)
client = MimirClient(intents=intents, is_sandbox=True, log_level=10, timeout=30)
appid = os.getenv("QQBOT_APP_ID")
secret = os.getenv("QQBOT_APP_SECRET")
client.run(appid=appid, secret=secret)
