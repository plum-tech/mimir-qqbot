import botpy
from botpy.manage import GroupManageEvent
from botpy.message import Message, DirectMessage, GroupMessage
import os

_log = botpy.logging.get_logger()


class MimirClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot[{self.robot.name}] is ready.")

    async def on_group_at_message_create(self, message: GroupMessage):
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
