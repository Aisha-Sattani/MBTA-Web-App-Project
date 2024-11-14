import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
MBTA_API_KEY = os.getenv("MBTA_API_KEY")

# Base URLs
MAPBOX_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
MBTA_BASE_URL = "https://api-v3.mbta.com"

def get_json(url: str) -> dict:
    """
    Given a properly formatted URL for a JSON web API request,
    return a Python JSON object containing the response to that request.
    """
    response = requests.get(url)
    response.raise_for_status()  # Check if request was successful
    return response.json()

def get_lat_lng(place_name: str) -> tuple[str, str]:
    """
    Given a place name or address, return a (latitude, longitude) tuple with
    the coordinates of the given place using the Mapbox Geocoding API.
    """
    url = f"{MAPBOX_BASE_URL}/{place_name}.json?access_token={MAPBOX_TOKEN}"
    data = get_json(url)
    # print(data) 
    
    # Extract latitude and longitude from the first result
    coordinates = data['features'][0]['geometry']['coordinates']
    longitude, latitude = coordinates[0], coordinates[1]
    return str(latitude), str(longitude)

def get_nearest_station(latitude: str, longitude: str) -> tuple[str, str, bool]:
    """
    Given latitude and longitude strings, return a (station_name, station_id, wheelchair_accessible)
    tuple for the nearest MBTA station to the given coordinates.
    """
    url = f"{MBTA_BASE_URL}/stops?api_key={MBTA_API_KEY}&filter[latitude]={latitude}&filter[longitude]={longitude}&sort=distance"
    data = get_json(url)
    
    # Extract the nearest station details
    if data['data']:
        nearest_stop = data['data'][0]
        station_name = nearest_stop['attributes']['name']
        station_id = nearest_stop['id']
        wheelchair_accessible = nearest_stop['attributes']['wheelchair_boarding'] == 1  # 1 means accessible
        return station_name, station_id, wheelchair_accessible
    else:
        return "No nearby station found", None, False

def get_real_time_arrivals(stop_id: str) -> list:
    """
    Given a stop ID, return a list of upcoming arrival times in minutes for that stop.
    """
    url = f"{MBTA_BASE_URL}/predictions?api_key={MBTA_API_KEY}&filter[stop]={stop_id}&sort=arrival_time"
    data = get_json(url)
    
    arrivals = []
    for item in data['data']:
        arrival_time = item['attributes']['arrival_time']
        if arrival_time:
            from datetime import datetime, timezone
            arrival_dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00')).astimezone(timezone.utc)
            now = datetime.now(timezone.utc)
            minutes_until_arrival = (arrival_dt - now).total_seconds() / 60
            if minutes_until_arrival > 0:
                arrivals.append(round(minutes_until_arrival))
    
    return arrivals

def find_stop_near(place_name: str) -> tuple[str, bool, list]:
    """
    Given a place name or address, return the nearest MBTA stop, whether it is
    wheelchair accessible, and a list of upcoming arrival times in minutes.
    """
    latitude, longitude = get_lat_lng(place_name)
    station_name, station_id, wheelchair_accessible = get_nearest_station(latitude, longitude)
    if station_id:
        arrivals = get_real_time_arrivals(station_id)
    else:
        arrivals = []
    return station_name, wheelchair_accessible, arrivals

def main():
    """
    Tests all the above functions.
    """
    place_name = input("Enter a place name or address: ")
    station_name, wheelchair_accessible, arrivals = find_stop_near(place_name)
    accessible_text = "is" if wheelchair_accessible else "is not"
    print(f"The nearest MBTA stop to '{place_name}' is '{station_name}', which {accessible_text} wheelchair accessible.")
    if arrivals:
        print(f"Upcoming arrivals in minutes: {', '.join(map(str, arrivals))}")
    else:
        print("No upcoming arrivals found.")

if __name__ == "__main__":
    main()
