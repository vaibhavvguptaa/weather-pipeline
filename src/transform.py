import pandas as pd
from src.logger import get_logger
from src.config import config

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation_probability",
    "windspeed_10m",
    "weathercode",
]

SCHEMA = {
    "temperature_2m": "float64",
    "relative_humidity_2m": "float64",
    "precipitation_probability": "float64",
    "windspeed_10m": "float64",
    "weathercode": "int64",
}


def parse_raw(raw: dict) -> pd.DataFrame:
    """Convert raw API JSON into a flat DataFrame."""
    hourly = raw.get("hourly", {})

    if not hourly:
        raise ValueError("API response missing 'hourly' key — unexpected schema")

    df = pd.DataFrame(hourly)
    logger.info(f"Parsed raw data — {len(df)} rows, {len(df.columns)} columns")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and type-cast the raw DataFrame."""

    # ── Schema check ──────────────────────────────────────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")

    df = df[REQUIRED_COLUMNS].copy()

    # ── Datetime parsing ──────────────────────────────────────────
    df["time"] = pd.to_datetime(df["time"])
    logger.debug("Parsed 'time' column to datetime")

    # ── Type casting ──────────────────────────────────────────────
    for col, dtype in SCHEMA.items():
        df[col] = df[col].astype(dtype)

    # ── Add derived columns ───────────────────────────────────────
    df["city"] = config.city_name
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour

    logger.info(f"Clean complete — {len(df)} rows, {df['date'].nunique()} days")
    return df


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run data quality checks. Raises on critical failures,
    logs warnings on non-critical issues.
    """
    errors = []
    warnings = []

    # ── Null checks ───────────────────────────────────────────────
    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            pct = round(count / len(df) * 100, 1)
            if pct > 20:
                errors.append(f"Column '{col}' has {pct}% nulls (threshold: 20%)")
            else:
                warnings.append(f"Column '{col}' has {count} nulls ({pct}%)")

    # ── Range checks ─────────────────────────────────────────────
    if not df["temperature_2m"].between(-50, 60).all():
        errors.append("temperature_2m has values outside plausible range [-50, 60]°C")

    if not df["relative_humidity_2m"].between(0, 100).all():
        errors.append("relative_humidity_2m out of range [0, 100]%")

    if not df["precipitation_probability"].between(0, 100).all():
        errors.append("precipitation_probability out of range [0, 100]%")

    # ── Row count check ───────────────────────────────────────────
    expected_rows = 7 * 24   # 7 days × 24 hours
    if len(df) < expected_rows * 0.9:
        errors.append(
            f"Row count {len(df)} is below 90% of expected {expected_rows}"
        )

    # ── Raise or warn ─────────────────────────────────────────────
    for w in warnings:
        logger.warning(f"[VALIDATION] {w}")

    if errors:
        for e in errors:
            logger.error(f"[VALIDATION FAILED] {e}")
        raise ValueError(f"Data validation failed with {len(errors)} error(s). "
                         f"See logs for details.")

    logger.info(f"Validation passed — {len(df)} rows, "
                f"{null_counts.sum()} total nulls")
    return df


def transform(raw: dict) -> pd.DataFrame:
    """Full transform pipeline: parse → clean → validate."""
    df = parse_raw(raw)
    df = clean(df)
    df = validate(df)
    return df