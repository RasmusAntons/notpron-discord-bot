from commands.command import Command
import discord
import pyowm
import datetime
import pyowm.commons.exceptions


class WeatherCommand(Command):
    name = 'weather'
    arg_range = (0, 99)
    description = 'get the current weather at a location'
    arg_desc = '<location>'

    async def execute(self, args, msg):
        query = ''.join(args)
        try:
            await msg.channel.send(embed=get_weather_msg(query, self.bot.config.get_owm_key(),
                                                         self.bot.config.get_embed_colour()))
        except pyowm.commons.exceptions.NotFoundError:
            await msg.channel.send(f'{msg.author.mention} I don\'t know that place')


def degrees_to_cardinal(d):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def get_weather_msg(query, owm_key, embed_colour):
    owm = pyowm.OWM(owm_key)
    mgr = owm.weather_manager()
    obs = mgr.weather_at_place(query)
    weather = obs.weather
    embed = discord.Embed(title=f'Weather {obs.location.name}, {obs.location.country}', color=embed_colour)
    embed.set_thumbnail(url=f'https://openweathermap.org/img/wn/{weather.weather_icon_name}@2x.png')
    temp_c = weather.temperature('celsius').get('temp')
    temp_f = weather.temperature('fahrenheit').get('temp')
    status = f'*{weather.detailed_status}*'
    wind_eu = weather.wind('km_hour')
    wind_eu_speed = wind_eu.get('speed')
    wind_us = weather.wind('miles_hour')
    wind_us_speed = wind_us.get('speed')
    wind_deg = wind_eu.get('deg')
    wind = f'Wind: {wind_eu_speed:0.2f}kph ({wind_us_speed:0.2f}mph) {degrees_to_cardinal(wind_deg)}'
    humidity = f'Humidity: {weather.humidity}%'
    srise = datetime.datetime.utcfromtimestamp(weather.sunrise_time() + weather.utc_offset).strftime('%H:%M')
    sset = datetime.datetime.utcfromtimestamp(weather.sunset_time() + weather.utc_offset).strftime('%H:%M')
    sun_info = f'Sunrise/Sunset: {srise}/{sset}'
    lat = f'{obs.location.lat:.3f}'.rstrip('0')
    lon = f'{obs.location.lon:.3f}'.rstrip('0')
    url = f'<https://www.google.com/maps/@{lat},{lon},12z>'
    embed.add_field(name=f'{temp_c}°C ({temp_f}°F)', value='\n'.join([status, wind, humidity, sun_info, url]), inline=False)
    local_time = datetime.datetime.utcfromtimestamp(obs.rec_time + weather.utc_offset).strftime('%b %d %H:%M')
    embed.set_footer(text=f'Local time: {local_time}')
    return embed
