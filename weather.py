import asyncio
from datetime import datetime

import aiohttp
import enum

import r


class WeatherLive:
    def __init__(self, *, province, city, weather, temperature, wind_direction, wind_power, humidity):
        self.province = province
        self.city = city
        self.weather = weather
        self.temperature = temperature
        self.wind_direction = wind_direction
        self.wind_power = wind_power
        self.humidity = humidity


class WeatherCastEntry:
    def __init__(self, *, weather, temperature, wind_direction, wind_power):
        self.weather = weather
        self.temperature = temperature
        self.wind_direction = wind_direction
        self.wind_power = wind_power

    @classmethod
    def from_cast(cls, cast, *, day: bool):
        p = "day" if day else "night"
        return WeatherCastEntry(
            weather=cast[f"{p}weather"],
            temperature=cast[f"{p}temp"],
            wind_direction=cast[f"{p}wind"],
            wind_power=cast[f"{p}power"],
        )

    @classmethod
    def from_day_cast(cls, cast):
        return cls.from_cast(cast, day=True)

    @classmethod
    def from_night_cast(cls, cast):
        return cls.from_cast(cast, day=False)


class WeatherCast:
    def __init__(self, *, date: datetime, day: WeatherCastEntry, night: WeatherCastEntry):
        self.date = date
        self.day = day
        self.night = night


class WeatherForcast:
    def __init__(self, *, province, city, casts: list[WeatherCast]):
        self.province = province
        self.city = city
        self.casts = casts


class City(enum.Enum):
    feng_xian = "310120"
    xu_hui = "310104"


async def fetch_live(session: aiohttp.ClientSession, city: City):
    async with session.get(
            f"https://restapi.amap.com/v3/weather/weatherInfo?city={city.value}&key={r.weather_api_token}"
    ) as res:
        if not res.ok:
            return
        result = await res.json()
        if result.get("status") != "1":
            return
        lives = result["lives"]
        if len(lives) <= 0:
            return
        live = lives[0]
        return WeatherLive(
            province=live["province"],
            city=live["city"],
            weather=live["weather"],
            temperature=live["temperature"],
            wind_direction=live["winddirection"],
            wind_power=live["windpower"],
            humidity=live["humidity"],
        )


async def fetch_forcast(session: aiohttp.ClientSession, city: City):
    async with session.get(
            f"https://restapi.amap.com/v3/weather/weatherInfo?city={city.value}&extensions=all&key={r.weather_api_token}"
    ) as res:
        if not res.ok:
            return
        result = await res.json()
        if result.get("status") != "1":
            return
        forecasts = result["forecasts"]
        if len(forecasts) <= 0:
            return
        forecast = forecasts[0]
        return WeatherForcast(
            province=forecast["province"],
            city=forecast["city"],
            casts=[
                WeatherCast(
                    date=datetime.strptime(cast["date"], "%Y-%m-%d"),
                    day=WeatherCastEntry.from_day_cast(cast),
                    night=WeatherCastEntry.from_night_cast(cast),
                )
                for cast in forecast["casts"]
            ],

        )


async def fetch(session: aiohttp.ClientSession, city: City):
    live, forcast = await asyncio.gather(
        fetch_live(session, city),
        fetch_forcast(session, city),
    )
    return live, forcast
