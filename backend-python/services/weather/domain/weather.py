"""
Weather Domain Entity
Pure business logic for weather data
"""

from typing import Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class WeatherCondition:
    """Weather condition value object (immutable)"""
    location: str
    temperature: float
    temperature_unit: str  # C or F
    condition: str
    humidity: int
    wind_speed: float
    wind_unit: str  # km/h or mph
    feels_like: float
    uv_index: int
    visibility: int
    pressure: int
    sunrise: str
    sunset: str
    icon: str
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Validation"""
        if not self.location or len(self.location.strip()) == 0:
            raise ValueError("Location is required")

        if self.temperature_unit not in ["C", "F"]:
            raise ValueError("Temperature unit must be C or F")

        if self.humidity < 0 or self.humidity > 100:
            raise ValueError("Humidity must be between 0 and 100")

        if self.uv_index < 0 or self.uv_index > 11:
            raise ValueError("UV index must be between 0 and 11")

        if self.wind_speed < 0:
            raise ValueError("Wind speed cannot be negative")

        if not self.timestamp:
            object.__setattr__(self, 'timestamp', datetime.now(timezone.utc))

    def is_hot(self) -> bool:
        """Check if temperature is hot (>30C or >86F)"""
        if self.temperature_unit == "C":
            return self.temperature > 30
        return self.temperature > 86

    def is_cold(self) -> bool:
        """Check if temperature is cold (<15C or <59F)"""
        if self.temperature_unit == "C":
            return self.temperature < 15
        return self.temperature < 59

    def is_rainy(self) -> bool:
        """Check if it's raining"""
        return "rain" in self.condition.lower() or "thunderstorm" in self.condition.lower()

    def is_sunny(self) -> bool:
        """Check if it's sunny"""
        return "sunny" in self.condition.lower() or "clear" in self.condition.lower()

    def is_cloudy(self) -> bool:
        """Check if it's cloudy"""
        return "cloud" in self.condition.lower()

    def is_high_uv(self) -> bool:
        """Check if UV index is high (>6)"""
        return self.uv_index > 6

    def is_windy(self) -> bool:
        """Check if it's windy (>20 km/h or >12 mph)"""
        if self.wind_unit == "km/h":
            return self.wind_speed > 20
        return self.wind_speed > 12

    def to_celsius(self) -> float:
        """Convert temperature to Celsius"""
        if self.temperature_unit == "C":
            return self.temperature
        return (self.temperature - 32) * 5 / 9

    def to_fahrenheit(self) -> float:
        """Convert temperature to Fahrenheit"""
        if self.temperature_unit == "F":
            return self.temperature
        return (self.temperature * 9 / 5) + 32


@dataclass(frozen=True)
class ForecastDay:
    """Weather forecast for a single day (immutable)"""
    day: int
    date: str
    high: float
    low: float
    condition: str
    precipitation: int  # Percentage
    humidity: int

    def __post_init__(self):
        """Validation"""
        if self.day < 0:
            raise ValueError("Day cannot be negative")

        if self.humidity < 0 or self.humidity > 100:
            raise ValueError("Humidity must be between 0 and 100")

        if self.precipitation < 0 or self.precipitation > 100:
            raise ValueError("Precipitation must be between 0 and 100")

        if self.high < self.low:
            raise ValueError("High temperature cannot be lower than low temperature")

    def is_rainy(self) -> bool:
        """Check if rain is expected"""
        return "rain" in self.condition.lower() or self.precipitation > 50

    def is_hot(self) -> bool:
        """Check if day will be hot (high > 30C)"""
        return self.high > 30

    def is_cold(self) -> bool:
        """Check if day will be cold (low < 15C)"""
        return self.low < 15


class WeatherForecast:
    """Weather forecast entity"""

    def __init__(
        self,
        location: str,
        forecast_days: List[ForecastDay],
        unit: str = "C",
        updated_at: Optional[datetime] = None,
    ):
        self.location = location
        self.forecast_days = forecast_days
        self.unit = unit
        self.updated_at = updated_at or datetime.now(timezone.utc)

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.location or len(self.location.strip()) == 0:
            raise ValueError("Location is required")

        if not self.forecast_days:
            raise ValueError("Forecast must have at least one day")

        if len(self.forecast_days) > 14:
            raise ValueError("Forecast cannot exceed 14 days")

        if self.unit not in ["C", "F"]:
            raise ValueError("Temperature unit must be C or F")

    def get_day(self, day_index: int) -> Optional[ForecastDay]:
        """Get forecast for specific day"""
        if 0 <= day_index < len(self.forecast_days):
            return self.forecast_days[day_index]
        return None

    def get_today(self) -> Optional[ForecastDay]:
        """Get today's forecast"""
        return self.get_day(0)

    def get_tomorrow(self) -> Optional[ForecastDay]:
        """Get tomorrow's forecast"""
        return self.get_day(1)

    def get_days_count(self) -> int:
        """Get number of forecast days"""
        return len(self.forecast_days)

    def get_rainy_days(self) -> List[ForecastDay]:
        """Get all rainy days in forecast"""
        return [day for day in self.forecast_days if day.is_rainy()]

    def get_hot_days(self) -> List[ForecastDay]:
        """Get all hot days in forecast"""
        return [day for day in self.forecast_days if day.is_hot()]

    def get_average_temperature(self) -> float:
        """Get average high temperature across all days"""
        if not self.forecast_days:
            return 0.0
        return sum(day.high for day in self.forecast_days) / len(self.forecast_days)

    def has_rain_in_forecast(self) -> bool:
        """Check if rain is expected in any day"""
        return any(day.is_rainy() for day in self.forecast_days)

    def is_fresh(self, max_age_minutes: int = 60) -> bool:
        """Check if forecast is still fresh"""
        now = datetime.now(timezone.utc)
        age_minutes = (now - self.updated_at).total_seconds() / 60
        return age_minutes < max_age_minutes

    def __repr__(self):
        return f"<WeatherForecast(location='{self.location}', days={len(self.forecast_days)}, unit={self.unit})>"
