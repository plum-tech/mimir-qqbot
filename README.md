# Mimir QQ Bot

## How to install
First, make sure you have installed the [Docker](https://www.docker.com/).


## How to run
Create a `docker-compose.yaml` file.
```yaml
services:
  bot:
    image: mimir-qqbot:latest
    container_name: mimir-qqbot
    environment:
      MIMIR_QQBOT_APP_ID: <your qq bot app id>
      MIMIR_QQBOT_APP_SECRET: <your qq bot app secret>
      # MIMIR_BACKEND_URL: <https://api.mysit.life by default>
      AMAP_WEATHER_API_TOKEN: <amap weather api token>
    restart: always
```