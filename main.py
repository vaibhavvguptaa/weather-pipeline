import sys
from src.logger import get_logger
from src.extract import fetch_weather
from src.transform import transform
from src.load import save_csv, save_sqlite

logger = get_logger("main")


def run():
    logger.info("=" * 60)
    logger.info("weather-pipeline  START")
    logger.info("=" * 60)

    try:
        # ── Extract ───────────────────────────────────────────────
        logger.info("[1/3] EXTRACT — fetching from Open-Meteo API")
        raw = fetch_weather()

        # ── Transform ─────────────────────────────────────────────
        logger.info("[2/3] TRANSFORM — cleaning and validating")
        df = transform(raw)

        # ── Load ──────────────────────────────────────────────────
        logger.info("[3/3] LOAD — writing outputs")
        csv_path = save_csv(df)
        db_path = save_sqlite(df)

        logger.info("=" * 60)
        logger.info("Pipeline completed successfully")
        logger.info(f"  CSV  → {csv_path}")
        logger.info(f"  DB   → {db_path}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Pipeline FAILED: {e}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    run()