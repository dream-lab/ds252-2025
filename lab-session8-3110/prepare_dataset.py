# ecommerce_features/feature_repo/scripts/prepare_dataset.py
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]  # -> ecommerce_features/feature_repo
RAW  = BASE / "data" / "raw" / "Amazon Sale Report.csv"
OUT  = BASE / "data" / "processed" / "sales.parquet"

def normalize_columns(cols):
    return [c.strip().lower().replace(" ", "_").replace("-", "_") for c in cols]

def coerce_amount(x):
    if pd.isna(x): return None
    if isinstance(x, str): x = x.replace(",", "").strip()
    try: return float(x)
    except: return None

def main():
    df = pd.read_csv(RAW, low_memory=False)
    df.columns = normalize_columns(df.columns)

    required = ["order_id", "date", "category", "qty", "amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Required columns missing: {missing}")

    out = df[required].copy().rename(columns={"date": "event_timestamp"})
    out["event_timestamp"] = pd.to_datetime(out["event_timestamp"], errors="coerce")
    out["order_id"] = out["order_id"].astype(str).str.strip()
    out["qty"] = pd.to_numeric(out["qty"], errors="coerce").astype("Int64")
    out["amount"] = out["amount"].apply(coerce_amount)
    out = out.dropna(subset=["order_id", "event_timestamp", "qty", "amount"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"✅ Wrote {OUT}")

if __name__ == "__main__":
    main()
