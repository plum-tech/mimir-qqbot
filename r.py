import os
from dotenv import load_dotenv
from str2bool3 import str2bool

load_dotenv()

sandboxed = str2bool(os.getenv("QQBOT_SANDBOX"))
if sandboxed:
    print("Bot is running in sandboxed environment.")
else:
    print("Bot is running in production environment.")

appid = os.getenv("QQBOT_APP_ID")
if appid is None:
    raise Exception('Missing "QQBOT_APP_ID" environment variable for your bot AppID')

secret = os.getenv("QQBOT_APP_SECRET")
if secret is None:
    raise Exception('Missing "QQBOT_APP_SECRET" environment variable for your AppSecret')

backend_elec = os.getenv("MIMIR_ELEC_URL", default="http://elec.api.mysit.life/v1")
backend_elec_token = os.getenv("MIMIR_ELEC_ADMIN_TOKEN")

weather_api_token = os.getenv("AMAP_WEATHER_API_TOKEN")
if weather_api_token is None:
    raise Exception('Missing "AMAP_WEATHER_API_TOKEN" environment variable for your AppSecret')

forum_token = os.getenv("MIMIR_FORUM_TOKEN")
if forum_token is None:
    raise Exception('Missing "MIMIR_FORUM_TOKEN" environment variable for your AppSecret')