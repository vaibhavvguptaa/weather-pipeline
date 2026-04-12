import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"

PARAMS = {
    "latitude": config.latitude,
    "longitude": config.longitude,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "windspeed_10m",
        "weathercode",
    ],
    "timezone": "Asia/Kolkata",
    "forecast_days": 7,
}


@retry(
    stop=stop_after_attempt(config.max_retries),
    wait=wait_exponential(multiplier=config.retry_backoff, min=2, max=30),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def fetch_weather() -> dict:
    """
    Fetch 7-day hourly forecast from Open-Meteo.
    Retries on connection errors with exponential backoff.
    """
    logger.info(f"Fetching weather data for {config.city_name} "
                f"({config.latitude}, {config.longitude})")

    response = requests.get(API_URL, params=PARAMS, timeout=10)
    response.raise_for_status()

    data = response.json()
    logger.info(f"API response received — status {response.status_code}")
    logger.debug(f"Raw API units: {data.get('hourly_units', {})}")

    return data