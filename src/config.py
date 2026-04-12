import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    latitude: float = float(os.getenv("LATITUDE", 28.6139))
    longitude: float = float(os.getenv("LONGITUDE", 77.2090))
    city_name: str = os.getenv("CITY_NAME", "Delhi")
    output_dir: str = os.getenv("OUTPUT_DIR", "data")
    db_name: str = os.getenv("DB_NAME", "weather.db")
    max_retries: int = int(os.getenv("MAX_RETRIES", 3))
    retry_backoff: int = int(os.getenv("RETRY_BACKOFF", 2))


config = Config()