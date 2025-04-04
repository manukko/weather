from datetime import datetime
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

def _parse_date_str_to_ts(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").timestamp()

def _get_coordinates_by_location(location: str):
    location = location.lower().capitalize()
    output = requests.get(
    url=f"{BASE_URL}/geo/1.0/direct?q={location}&limit=5&appid={API_KEY}"
    )
    if output.status_code != 200 or not output.json():
        raise HTTPException(status_code=output.status_code, detail="Call to weather geolocation service failed; did you type a valid location name?")
    return output.json()[0]["lon"], output.json()[0]["lat"]

def _get_current_weather_by_coordinates(lon: float, lat: float):
    output = requests.get(
    url=f"{BASE_URL}/data/2.5/weather?lon={lon}&lat={lat}&units=metric&appid={API_KEY}"
    )
    if output.status_code != 200:
        raise HTTPException(status_code=output.status_code, detail="Call to weather data service failed")
    return output.json()

def _get_weather_forecast_by_location(lon: float, lat: float, forecast_date_ts: int | None = None):
    output = requests.get(
    url=f"{BASE_URL}/data/2.5/forecast?lon={lon}&lat={lat}&units=metric&appid={API_KEY}"
    )
    if output.status_code != 200:
        raise HTTPException(status_code=output.status_code, detail="Call to weather data service failed")
    if forecast_date_ts is not None:
        desired_forecast = None
        print(f"forecast_date_ts:{forecast_date_ts}")
        for entry in output.json()["list"]:
            if entry["dt"] <= forecast_date_ts and entry["dt"] + 3*3600 >= forecast_date_ts:
                desired_forecast = entry
                break
        if not desired_forecast:
            raise HTTPException(status_code=404, detail="Invalid request date: did you type a date in the past or too far in the future?")
        json_output = output.json()
        del json_output["list"]
        json_output["forecast"] = desired_forecast
    else:
        json_output = output.json()
    return json_output

@app.get("/get_current_weather_by_coordinates")
def get_current_weather_by_coordinates(lon: float = Query(title="longitude"), lat: float = Query(title="latitude")):
    return _get_current_weather_by_coordinates(lon, lat)

@app.get("/get_current_weather_by_location")
def get_current_weather_by_location(location: str = Query(title="Geographical location")):
    lon, lat = _get_coordinates_by_location(location)
    return _get_current_weather_by_coordinates(lon, lat)


@app.get("/get_weather_forecast_by_coordinates")
def get_weather_forecast_by_coordinates(lon: float = Query(title="longitude"), lat: float = Query(title="latitude"), forecast_date_string: str | None = Query(default=None, title="Date of the forecast in format YYYY-MM-DD hh:mm:ss", alias="date")):
    forecast_date_ts = None
    if forecast_date_string:
        try:
            forecast_date_ts = _parse_date_str_to_ts(forecast_date_string)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
    return _get_weather_forecast_by_location(lon, lat, forecast_date_ts)

@app.get("/get_weather_forecast_by_location")
def get_weather_forecast_by_location(location: str = Query(title="Geographical location"), forecast_date_string: str | None = Query(default=None, title="Date of the forecast in format YYYY-MM-DD hh:mm:ss utc", alias="date")):
    forecast_date_ts = None
    if forecast_date_string:
        try:
            forecast_date_ts = _parse_date_str_to_ts(forecast_date_string)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
    lon, lat = _get_coordinates_by_location(location)
    return _get_weather_forecast_by_location(lon, lat, forecast_date_ts)

