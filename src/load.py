import sqlite3
import pandas as pd
from pathlib import Path
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


def _ensure_output_dir() -> Path:
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_csv(df: pd.DataFrame) -> Path:
    """Save DataFrame to a date-stamped CSV file."""
    out_dir = _ensure_output_dir()
    run_date = df["date"].min()   # earliest date in the batch
    filename = out_dir / f"weather_{config.city_name.lower()}_{run_date}.csv"

    df.to_csv(filename, index=False)
    logger.info(f"CSV saved → {filename}  ({len(df)} rows)")
    return filename


def save_sqlite(df: pd.DataFrame) -> Path:
    """
    Upsert DataFrame into SQLite.
    Uses INSERT OR REPLACE so re-running the pipeline is idempotent.
    """
    out_dir = _ensure_output_dir()
    db_path = out_dir / config.db_name

    with sqlite3.connect(db_path) as conn:
        # Create table with a composite primary key so re-runs don't duplicate
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecast (
                time                     TEXT,
                city                     TEXT,
                temperature_2m           REAL,
                relative_humidity_2m     REAL,
                precipitation_probability REAL,
                windspeed_10m            REAL,
                weathercode              INTEGER,
                date                     TEXT,
                hour                     INTEGER,
                PRIMARY KEY (time, city)
            )
        """)

        # Convert date column to string for SQLite compatibility
        df_load = df.copy()
        df_load["time"] = df_load["time"].astype(str)
        df_load["date"] = df_load["date"].astype(str)

        # Load into a temporary staging table to support idempotent upserts
        df_load.to_sql(
            "temp_weather_forecast",
            conn,
            if_exists="replace",
            index=False,
            method="multi",
        )

        # Upsert from staging table into the primary table
        conn.execute("""
            INSERT OR REPLACE INTO weather_forecast (
                time, city, temperature_2m, relative_humidity_2m,
                precipitation_probability, windspeed_10m, weathercode, date, hour
            )
            SELECT 
                time, city, temperature_2m, relative_humidity_2m,
                precipitation_probability, windspeed_10m, weathercode, date, hour
            FROM temp_weather_forecast
        """)

        # Clean up staging table
        conn.execute("DROP TABLE temp_weather_forecast")
        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM weather_forecast"
        ).fetchone()[0]

    logger.info(f"SQLite saved → {db_path}  (total rows in DB: {count})")
    return db_path
