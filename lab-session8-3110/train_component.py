# train_component.py
import argparse, os, json, joblib, urllib.parse
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import boto3

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-parquet", required=True)
    p.add_argument("--model-s3-uri", required=True)
    p.add_argument("--target", default="amount", choices=["amount","category"])
    return p.parse_args()

def main():
    args = parse_args()
    df = pd.read_parquet(args.input_parquet)

    if args.target == "amount":
        X = df[["qty"]]
        y = df["amount"]
        model = RandomForestRegressor(n_estimators=60, random_state=42)
    else:
        X = df[["qty"]]
        y = df["category"].astype("category").cat.codes
        model = RandomForestClassifier(n_estimators=100, random_state=42)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(Xtr, ytr)

    os.makedirs("/out", exist_ok=True)
    local_path = "/out/model.joblib"
    joblib.dump(model, local_path)

    parsed = urllib.parse.urlparse(args.model_s3_uri)
    boto3.client("s3").upload_file(local_path, parsed.netloc, parsed.path.lstrip("/"))
    print("MODEL_URI:", args.model_s3_uri)

    # Optional: write KFP metrics file if you want them in UI
    # import numpy as np
    # from sklearn.metrics import r2_score, accuracy_score
    # ...

if __name__ == "__main__":
    main()
