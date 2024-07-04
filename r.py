import os
from dotenv import load_dotenv

load_dotenv()

appid = os.getenv("QQBOT_APP_ID")
if appid is None:
    raise Exception('Missing "QQBOT_APP_ID" environment variable for your bot AppID')

secret = os.getenv("QQBOT_APP_SECRET")
if secret is None:
    raise Exception('Missing "QQBOT_APP_SECRET" environment variable for your AppSecret')

backend = os.getenv("MIMIR_BACKEND_URL", default="http://api.mysit.life")

WeatherApiToken = os.getenv("WEATHER_API_TOKEN")
if MCServerHost is None:
    raise Exception('Missing "WEATHER_API_TOKEN" environment variable for your AppSecret')
