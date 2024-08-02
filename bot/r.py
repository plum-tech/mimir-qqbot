import os
from dotenv import load_dotenv

load_dotenv()

appid = os.getenv("MIMIR_QQBOT_APP_ID")
if appid is None:
    raise Exception('Missing "MIMIR_QQBOT_APP_ID" environment variable for your bot AppID')

secret = os.getenv("MIMIR_QQBOT_APP_SECRET")
if secret is None:
    raise Exception('Missing "MIMIR_QQBOT_APP_SECRET" environment variable for your AppSecret')

backend = os.getenv("MIMIR_BACKEND_URL", default="http://elec.api.mysit.life/v1")
backend_elec_token = os.getenv("MIMIR_BACKEND_ELEC_TOKEN")

weather_api_token = os.getenv("AMAP_WEATHER_API_TOKEN")
if weather_api_token is None:
    raise Exception('Missing "AMAP_WEATHER_API_TOKEN" environment variable for your AppSecret')
