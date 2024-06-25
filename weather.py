import requests
import datetime
import configparser


config = configparser.ConfigParser()
config.read("settings.ini")

api_key = config.get("Secure","token")


city = config["Default"]["city"]


def get_geo(city):
    r = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    )

    data = r.json()
    lon = data[0]['lon']
    lat = data[0]['lat']
    # pprint(data, lon, lat)
    return lat, lon


def get_weather():
    lat = get_geo(city)[0]
    lon = get_geo(city)[1]

    r_now = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=ru&appid={api_key}"
    )

    r_forecast = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&lang=ru&appid={api_key}"
    )

    data_now = r_now.json()
    # pprint(data_now)
    data_forecast = r_forecast.json()
    # pprint(data_forecast)

    icon_now = data_now["weather"][0]["icon"]

    # Получаем картинку с погодой
    icon_url = f"http://openweathermap.org/img/wn/{icon_now}@2x.png"
    icon_response = requests.get(icon_url)
    icon_image = icon_response.content

    # Создаем словарь для хранения информации о погоде
    weather_forecast = {}
    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time().strftime("%H:%M")

    weather_forecast[current_time] = {
        "feels_like": data_now["main"]["feels_like"],
        "temperature": data_now["main"]["temp"],
        "humidity": data_now["main"]["humidity"],
        "wind_speed": data_now["wind"]["speed"],
        "description": data_now["weather"][0]["description"],
        "icon": icon_image

    }


    for forecast in data_forecast["list"]:
        forecast_date = datetime.datetime.fromtimestamp(forecast["dt"])
        if forecast_date.date() == current_date:
            icon_forecast = forecast["weather"][0]["icon"]
            icon_url = f"http://openweathermap.org/img/wn/{icon_forecast}@2x.png"
            icon_response = requests.get(icon_url)
            icon_image = icon_response.content

            weather_forecast[forecast_date.strftime("%H:%M")] = {
                "feels_like": forecast["main"]["feels_like"],
                "temperature": forecast["main"]["temp"],
                "humidity": forecast["main"]["humidity"],
                "wind_speed": forecast["wind"]["speed"],
                "description": forecast["weather"][0]["description"],
                "icon": icon_image
            }

    return weather_forecast

weather_forecast = get_weather()
# pprint(weather_forecast)
# get_weather(api_key)
