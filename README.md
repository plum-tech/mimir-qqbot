# SIT Life QQ Bot

## How to install
First, make sure you have installed the [Docker](https://www.docker.com/).

## How to build
```bash
docker build . -t cr.liplum.net/mimir/qqbot:<tag>
docker push cr.liplum.net/mimir/qqbot:<tag>
```

## How to run
Create a `docker-compose.yaml` file.
```yaml
services:
  bot:
    image: cr.liplum.net/mimir/qqbot:<tag>
    container_name: mimir.qqbot
    environment:
      QQBOT_SANDBOX: <0 or 1>
      QQBOT_APP_ID: <your qq bot app id>
      QQBOT_APP_SECRET: <your qq bot app secret>
      MIMIR_ELEC_ELEVATED_TOKEN: <backend elec token>
      AMAP_WEATHER_API_TOKEN: <amap weather api token>
    restart: always
```