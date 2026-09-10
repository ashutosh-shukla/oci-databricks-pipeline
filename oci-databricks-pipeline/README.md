<<<<<<< HEAD
# oci-databricks-pipeline

A pipeline that reads data from Databricks (Delta tables / volumes),
transforms it, and loads it into Oracle Autonomous Database (OCI ADB).

## Structure

- `src/extract/` — Databricks read logic
- `src/transform/` — cleaning and schema-mapping logic
- `src/load/` — Oracle ADB write logic
- `src/utils/` — logging and secrets helpers
- `src/pipeline.py` — orchestrates extract -> transform -> load
- `config/` — per-environment connection configuration (no secrets)
- `notebooks/` — ad-hoc exploration in Databricks
- `tests/` — unit tests
- `wallet/` — OCI DB wallet files (gitignored, never commit)

## Setup

1. Copy `.env.example` to `.env` and fill in real credentials.
2. Place your OCI wallet files in `wallet/` (never commit these).
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running

Run `src/pipeline.py` from a Databricks notebook or job context where a
Spark session is available, passing the appropriate `config/config.<env>.yaml`.

## Testing

```bash
pytest tests/
```

## CI

`.github/workflows/ci.yml` lints and tests on every push/PR to `main`.
=======
# oci-databricks-pipeline
>>>>>>> 00e0eda8a5b37fcfadb1d302f2d409cd12851401
