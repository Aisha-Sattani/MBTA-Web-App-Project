from flask import Flask, render_template, request, redirect, url_for
from mbta_helper import find_stop_near
from dotenv import load_dotenv
import requests
import os
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API keys from environment variables
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
HOLIDAYS_API_KEY = os.getenv("ABSTRACT_HOLIDAYS_API_KEY")

# Function to get current weather
def get_weather(city="Boston"):
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(weather_url)
        data = response.json()
        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"].capitalize()
        return f"{temperature}°C, {description}"
    except:
        return "Weather data not available"

def get_current_date():
    """ Function to get current date. """
    return datetime.now().strftime("%A, %B %d, %Y")

def get_today_holiday(country="US"):
    """
    Fetches today's public holiday for the specified country.
    If today is not a holiday, it returns a message indicating no holiday.
    """
    if not HOLIDAYS_API_KEY:
        return "Holiday data not available"

    today = datetime.now().strftime("%Y-%m-%d")
    holidays_url = f"https://holidays.abstractapi.com/v1/?api_key={HOLIDAYS_API_KEY}&country={country}&year={datetime.now().year}&month={datetime.now().month}&day={datetime.now().day}"

    try:
        response = requests.get(holidays_url)
        response.raise_for_status()
        holidays = response.json()

        # Check if today is a holiday
        for holiday in holidays:
            # if holiday["date"] == today:
            return f"Today is {holiday['name']}!"
        return "Today is not a holiday."
    except requests.exceptions.RequestException as e:
        print(f"Error fetching holiday data: {e}")
        return "Holiday data not available"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        place_name = request.form.get("place_name")
        if place_name:
            return redirect(url_for("nearest_mbta", place_name=place_name))
        else:
            return redirect(url_for("error"))
    
    # Pass the date, weather, and holiday info to the template
    date_today = get_current_date()
    weather_today = get_weather()
    next_holiday = get_today_holiday()
    return render_template("index.html", date_today=date_today, weather_today=weather_today, next_holiday=next_holiday)

@app.route("/nearest_mbta", methods=["GET"])
def nearest_mbta():
    place_name = request.args.get("place_name")
    if not place_name:
        return redirect(url_for("error"))

    try:
        station_name, wheelchair_accessible, arrivals = find_stop_near(place_name)
        date_today = get_current_date()
        weather_today = get_weather()
        next_holiday = get_today_holiday()
        return render_template("mbta_station.html", station_name=station_name, wheelchair_accessible=wheelchair_accessible, arrivals=arrivals, date_today=date_today, weather_today=weather_today, next_holiday=next_holiday)
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for("error"))

@app.route("/error")
def error():
    date_today = get_current_date()
    weather_today = get_weather()
    next_holiday = get_today_holiday()
    return render_template("error.html", date_today=date_today, weather_today=weather_today, next_holiday=next_holiday)

if __name__ == "__main__":
    app.run(debug=True)
