import discord
import pyowm


def degrees_to_cardinal(d):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def get_weather_msg(query, owm_key):
    owm = pyowm.OWM(owm_key)
    mgr = owm.weather_manager()
    obs = mgr.weather_at_place(query)
    weather = obs.weather
    embed = discord.Embed(title=f'Weather {obs.location.name}', color=0xa6ce86)
    embed.set_thumbnail(url=f'https://openweathermap.org/img/wn/{weather.weather_icon_name}@2x.png')
    temp_c = weather.temperature('celsius').get('temp')
    temp_f = weather.temperature('fahrenheit').get('temp')
    status = f'{weather.detailed_status}'
    wind_eu = weather.wind('km_hour')
    wind_eu_speed = wind_eu.get('speed')
    wind_us = weather.wind('miles_hour')
    wind_us_speed = wind_us.get('speed')
    wind_deg = wind_eu.get('deg')
    print(wind_eu)
    wind = f'Wind: {wind_eu_speed:0.3f}kph ({wind_us_speed:0.3f}mph) {degrees_to_cardinal(wind_deg)}'
    humidity = f'Humidity: {weather.humidity}%'
    embed.add_field(name=f'{temp_c}°C ({temp_f}°F)', value='\n'.join([status, wind, humidity]), inline=False)
    return embed
