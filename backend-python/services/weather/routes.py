"""
Weather Service Routes
Mock weather data for template processing
"""

from fastapi import APIRouter, Query
from typing import Optional
import random

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/current")
def get_current_weather(
    location: Optional[str] = Query("Jakarta", description="Location for weather data")
):
    """
    Get current weather data (mock for now)
    
    This endpoint returns mock weather data for template processing.
    In production, this would integrate with a real weather API.
    """
    
    # Mock weather conditions
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Thunderstorm"]
    
    # Generate mock data based on location
    temp_base = 28 if "jakarta" in location.lower() else 25
    
    return {
        "location": location,
        "temperature": temp_base + random.randint(-5, 5),
        "temperature_unit": "C",
        "condition": random.choice(conditions),
        "humidity": random.randint(60, 90),
        "wind_speed": random.randint(5, 20),
        "wind_unit": "km/h",
        "feels_like": temp_base + random.randint(-3, 3),
        "uv_index": random.randint(1, 11),
        "visibility": random.randint(5, 10),
        "pressure": random.randint(1005, 1020),
        "sunrise": "06:00",
        "sunset": "18:00",
        "icon": "sunny" if random.random() > 0.5 else "cloudy",
    }


@router.get("/forecast")
def get_weather_forecast(
    location: Optional[str] = Query("Jakarta", description="Location for weather data"),
    days: int = Query(5, ge=1, le=7, description="Number of forecast days")
):
    """
    Get weather forecast (mock for now)
    """
    
    forecast = []
    temp_base = 28 if "jakarta" in location.lower() else 25
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Thunderstorm"]
    
    for i in range(days):
        forecast.append({
            "day": i,
            "date": f"Day {i+1}",
            "high": temp_base + random.randint(2, 8),
            "low": temp_base - random.randint(2, 5),
            "condition": random.choice(conditions),
            "precipitation": random.randint(0, 80),
            "humidity": random.randint(60, 90),
        })
    
    return {
        "location": location,
        "forecast": forecast,
        "unit": "C",
    }