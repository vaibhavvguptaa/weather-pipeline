# weather-pipeline 🌤

A production-style ETL pipeline that fetches 7-day hourly weather forecast data for Delhi from the [Open-Meteo API](https://open-meteo.com), cleans and validates it with Pandas, and loads it into CSV + SQLite — with structured logging, retry logic, and data quality checks throughout.

> **Runs automatically every day at 6:00 AM IST via GitHub Actions.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        weather-pipeline                         │
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐ │
│   │   EXTRACT    │───▶│  TRANSFORM   │───▶│      LOAD        │ │
│   │              │    │              │    │                  │ │
│   │ Open-Meteo   │    │ Pandas clean │    │ CSV (dated)      │ │
│   │ API (free)   │    │ Type casting │    │ SQLite (upsert)  │ │
│   │              │    │ Null checks  │    │                  │ │
│   │ Tenacity     │    │ Range checks │    │ Idempotent —     │ │
│   │ retry logic  │    │ Row count    │    │ safe to re-run   │ │
│   └──────────────┘    └──────────────┘    └──────────────────┘ │
│                                                                 │
│   Structured logging (console + file) · .env config · venv     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   GitHub Actions   │
                    │  Cron: 6 AM IST    │
                    │  daily auto-run    │
                    └────────────────────┘
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| HTTP client | `requests` |
| Retry logic | `tenacity` (exponential backoff) |
| Data processing | `pandas` |
| Config management | `python-dotenv` |
| Storage | CSV + SQLite (`sqlite3`) |
| Logging | Python `logging` (console + rotating file) |
| Automation | GitHub Actions (daily cron) |

---

## Project Structure

```
weather-pipeline/
├── .env.example          # Config template (copy to .env)
├── .gitignore
├── requirements.txt
├── main.py               # Pipeline orchestrator
├── src/
│   ├── config.py         # Loads .env into a dataclass
│   ├── extract.py        # API fetch with retry logic
│   ├── transform.py      # Pandas clean + validate
│   ├── load.py           # CSV + SQLite writer (idempotent)
│   └── logger.py         # Structured logging setup
├── data/                 # Output files (gitignored)
│   ├── weather_delhi_YYYY-MM-DD.csv
│   └── weather.db
└── logs/                 # Log files (gitignored)
    └── pipeline.log
```

---

## Quickstart

### 1. Clone and set up environment

```bash
git clone https://github.com/vaibhavvvguptaa/weather-pipeline.git
cd weather-pipeline

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env if you want a different city (change LATITUDE, LONGITUDE, CITY_NAME)
```

### 3. Run

```bash
python main.py
```

### Expected output

```
2026-04-12 06:00:01 | INFO     | main | ============================================================
2026-04-12 06:00:01 | INFO     | main | weather-pipeline  START
2026-04-12 06:00:01 | INFO     | main | [1/3] EXTRACT — fetching from Open-Meteo API
2026-04-12 06:00:02 | INFO     | src.extract | Fetching weather data for Delhi (28.6139, 77.209)
2026-04-12 06:00:02 | INFO     | src.extract | API response received — status 200
2026-04-12 06:00:02 | INFO     | main | [2/3] TRANSFORM — cleaning and validating
2026-04-12 06:00:02 | INFO     | src.transform | Parsed raw data — 168 rows, 5 columns
2026-04-12 06:00:02 | INFO     | src.transform | Clean complete — 168 rows, 7 days
2026-04-12 06:00:02 | INFO     | src.transform | Validation passed — 168 rows, 0 total nulls
2026-04-12 06:00:02 | INFO     | main | [3/3] LOAD — writing outputs
2026-04-12 06:00:02 | INFO     | src.load | CSV saved → data/weather_delhi_2026-04-12.csv (168 rows)
2026-04-12 06:00:02 | INFO     | src.load | SQLite saved → data/weather.db (total rows in DB: 168)
2026-04-12 06:00:02 | INFO     | main | Pipeline completed successfully
```

---

## Data Quality Checks

The `transform.py` validation layer runs these checks on every execution:

| Check | Rule | Behaviour |
|---|---|---|
| Null check | Any column > 20% nulls | ❌ Raises error, pipeline stops |
| Null check | Any column ≤ 20% nulls | ⚠️ Logged as warning, continues |
| Temperature range | Must be between -50°C and 60°C | ❌ Raises error |
| Humidity range | Must be between 0% and 100% | ❌ Raises error |
| Precipitation range | Must be between 0% and 100% | ❌ Raises error |
| Row count | Must be ≥ 90% of expected 168 rows | ❌ Raises error |

---

## Key Engineering Decisions

**Idempotency** — re-running the pipeline on the same day produces the same result. SQLite uses a composite primary key `(time, city)` and deduplicates on every run. Safe to run multiple times.

**Retry with exponential backoff** — `tenacity` retries up to 3 times on `ConnectionError` or `Timeout`, with wait times of 2s → 4s → 8s before re-raising. Handles transient API failures gracefully.

**Structured logging** — every stage logs to both console (INFO+) and a persistent `logs/pipeline.log` file (DEBUG+). Easy to debug failures in production.

**Config via dataclass** — all configuration is loaded from `.env` into a typed `Config` dataclass. No hardcoded values anywhere in the pipeline code.

---

## Sample Output (CSV)

| time | temperature_2m | relative_humidity_2m | precipitation_probability | windspeed_10m | weathercode | city | date | hour |
|---|---|---|---|---|---|---|---|---|
| 2026-04-12 00:00:00 | 24.3 | 58.0 | 5.0 | 12.4 | 1 | Delhi | 2026-04-12 | 0 |
| 2026-04-12 01:00:00 | 23.8 | 61.0 | 5.0 | 10.2 | 0 | Delhi | 2026-04-12 | 1 |

---

## Author

**Vaibhav Gupta** — Technical Support Analyst Analyst at Highspring India LLP

[![LinkedIn](https://img.shields.io/badge/LinkedIn-vaibhavvvgupta-blue)](https://linkedin.com/in/vaibhavvvgupta)
[![GitHub](https://img.shields.io/badge/GitHub-vaibhavvvguptaa-black)](https://github.com/vaibhavvvguptaa)