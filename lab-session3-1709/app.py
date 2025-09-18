import os
import time
import hashlib
from datetime import datetime, timezone

from flask import Flask, request, Response, jsonify
import boto3
from botocore.exceptions import ClientError

APP_NAME = "ds252-flask"
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BUCKET = os.environ.get("S3_BUCKET")

# Fixed hashing workload (env knobs only; NOT per-request)
HASH_ROUNDS = int(os.environ.get("MICRO_HASH_ROUNDS", "50000"))  # total sha256 iterations

s3 = boto3.client("s3", region_name=REGION) if REGION else boto3.client("s3")
app = Flask(__name__)

def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status

def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "app": APP_NAME, "time_utc": _utc_now_iso(),
                    "bucket": BUCKET, "region": REGION, "pid": os.getpid()})

@app.get("/info")
def info():
    return jsonify({"app": APP_NAME, "env": {
        "AWS_REGION": REGION, "S3_BUCKET": BUCKET,
        "MICRO_HASH_ROUNDS": HASH_ROUNDS
    }})

@app.route("/hash", methods=["GET", "POST"])
def hash_endpoint():
    """
    Hashes a client-provided string with fixed CPU work:
      - Input string in 'data' (form field, JSON body, or query param).
      - Computes sha256(data), then repeats hashing HASH_ROUNDS-1 times.
    No time/size controls in the request; tune globally via MICRO_HASH_ROUNDS.
    """
    # Accept JSON, form, or query param
    if request.method == "POST":
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            data_val = payload.get("data")
        else:
            data_val = request.form.get("data")
    else:
        data_val = request.args.get("data")

    if data_val is None:
        return _json_error("Missing 'data' (provide as form field, JSON {data:...}, or ?data=)")

    t0 = time.perf_counter_ns()
    d = hashlib.sha256(data_val.encode("utf-8")).digest()
    for _ in range(max(1, HASH_ROUNDS) - 1):
        d = hashlib.sha256(d).digest()
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6

    return jsonify({
        "ok": True,
        "endpoint": "/hash",
        "started_utc": _utc_now_iso(),
        "input_len": len(data_val),
        "rounds": HASH_ROUNDS,
        "digest_hex": d.hex(),
        "timings_ms": {"total_ms": round(elapsed_ms, 3)}
    })

@app.get("/work")
def work():
    if not BUCKET:
        return _json_error("S3_BUCKET env var not set on server", 500)
    mode = request.args.get("mode", "").lower()
    key = request.args.get("key")
    if not key:
        return _json_error("Missing 'key'")
    try:
        if mode == "write":
            size_kb = int(request.args.get("size_kb", "64"))
            payload = os.urandom(size_kb * 1024)
            put = s3.put_object(Bucket=BUCKET, Key=key, Body=payload)
            return jsonify({"ok": True, "action": "write", "bucket": BUCKET, "key": key,
                            "size_kb": size_kb, "etag": put.get("ETag"), "version_id": put.get("VersionId")})
        elif mode == "read":
            obj = s3.get_object(Bucket=BUCKET, Key=key)
            data = obj["Body"].read()
            return jsonify({"ok": True, "action": "read", "bucket": BUCKET, "key": key,
                            "bytes": len(data), "preview_first_128_bytes_hex": data[:128].hex(),
                            "version_id": obj.get("VersionId")})
        else:
            return _json_error("Invalid mode. Use mode=write or mode=read.")
    except ClientError as e:
        err = e.response.get("Error", {})
        return _json_error(f"S3 error: {err.get('Code')} - {err.get('Message')}", 502 if mode == "write" else 404)

@app.route("/text", methods=["POST", "GET"])
def text():
    if not BUCKET:
        return _json_error("S3_BUCKET env var not set on server", 500)
    if request.method == "POST":
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            key = payload.get("key"); text_value = payload.get("text", "")
        else:
            key = request.form.get("key"); text_value = request.form.get("text", "")
        if not key:
            return _json_error("Missing 'key'")
        try:
            put = s3.put_object(Bucket=BUCKET, Key=key,
                                Body=text_value.encode("utf-8"),
                                ContentType="text/plain; charset=utf-8")
            return jsonify({"ok": True, "action": "write_text", "bucket": BUCKET, "key": key,
                            "bytes": len(text_value.encode('utf-8')),
                            "etag": put.get("ETag"), "version_id": put.get("VersionId")})
        except ClientError as e:
            err = e.response.get("Error", {})
            return _json_error(f"S3 error: {err.get('Code')} - {err.get('Message')}", 502)
    key = request.args.get("key")
    if not key:
        return _json_error("Missing 'key'")
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        return Response(obj["Body"].read(), status=200, mimetype="text/plain; charset=utf-8")
    except ClientError as e:
        err = e.response.get("Error", {})
        return _json_error(f"S3 error: {err.get('Code')} - {err.get('Message')}", 404)

@app.get("/")
def root():
    return jsonify({
        "message": "OK",
        "endpoints": {
            "/healthz": "GET health",
            "/hash": "POST/GET hash 'data' with fixed rounds; returns digest & latency",
            "/work": "GET S3 I/O: mode=write/read, key=..., size_kb=...",
            "/text": "POST {key,text} or GET ?key=..."
        }
    })

if __name__ == "__main__":
    # Local dev only. In containers, run: gunicorn -w 1 -b 0.0.0.0:5000 app:app
    app.run(host="0.0.0.0", port=5000, debug=False)
