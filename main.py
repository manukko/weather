import env
import requests
import fastapi
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import json

class PrettyJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content, indent=4, ensure_ascii=False).encode("utf-8")

app = FastAPI(default_response_class=PrettyJSONResponse)

API_KEY=env.API_KEY
BASE_URL = "https://api.openweathermap.org"

def _get_coordinates_by_location(location: str):
    location = location.lower().capitalize()
    output = requests.get(
    url=f"{BASE_URL}/geo/1.0/direct?q={location}&limit=5&appid={API_KEY}"
    )
    if output.status_code != 200 or not output.json():
        raise HTTPException(status_code=output.status_code, detail="Call to weather geolocation service failed; did you type a valid location name?")
    return output.json()[0]["lon"], output.json()[0]["lat"]

def _get_weather_by_coordinates(lon: float, lat: float):
    output = requests.get(
    url=f"{BASE_URL}/data/2.5/weather?lon={lon}&lat={lat}&units=metric&appid={API_KEY}"
    )
    if output.status_code != 200:
        raise HTTPException(status_code=output.status_code, detail="Call to weather data service failed")
    return output.json()

@app.get("/get_weather_by_coordinates")
def get_weather_by_coordinates(lon: float = Query(title="longitude"), lat: float = Query(title="latitude")):
    return _get_weather_by_coordinates(lon, lat)

@app.get("/get_weather_by_location")
def get_weather_by_location(location: str = Query(title="Geographical location")):
    lon, lat = _get_coordinates_by_location(location)
    return _get_weather_by_coordinates(lon, lat)