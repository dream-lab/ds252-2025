import os
import time
import secrets
import logging
from typing import Optional, Dict

from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import ClientError

APP_NAME = os.getenv("APP_NAME", "ds252-flask")
S3_BUCKET = os.getenv("S3_BUCKET")  # REQUIRED
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
PORT = int(os.getenv("PORT", "5000"))

if not S3_BUCKET:
    raise RuntimeError("Environment variable S3_BUCKET is required.")

s3 = boto3.client("s3", region_name=AWS_REGION)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger(APP_NAME)

app = Flask(__name__)

def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream",
              metadata: Optional[Dict[str, str]] = None) -> Dict:
    extra = {"ContentType": content_type}
    if metadata:
        extra["Metadata"] = metadata
    resp = s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, **extra)
    return {"bucket": S3_BUCKET, "key": key, "versionId": resp.get("VersionId"), "etag": resp.get("ETag")}

def get_bytes(key: str, version_id: Optional[str] = None) -> Dict:
    args = {"Bucket": S3_BUCKET, "Key": key}
    if version_id:
        args["VersionId"] = version_id
    obj = s3.get_object(**args)
    body = obj["Body"].read()
    return {
        "bucket": S3_BUCKET,
        "key": key,
        "versionId": obj.get("VersionId"),
        "etag": obj.get("ETag"),
        "contentType": obj.get("ContentType", "application/octet-stream"),
        "contentLength": len(body),
        "data": body,
        "lastModified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
        "metadata": obj.get("Metadata", {}),
    }

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "service": APP_NAME, "bucket": S3_BUCKET, "region": AWS_REGION})

@app.get("/")
def root():
    return jsonify({
        "message": "DS252 Flask + S3",
        "endpoints": {
            "health": "/healthz",
            "write text": "POST /text  {key, text, metadata?}",
            "read text": "GET /text/<key>?versionId=",
            "list": "GET /list?prefix=",
            "list versions": "GET /list-versions?prefix=",
            "delete": "DELETE /object/<key>?versionId=",
            "work (load test)": "GET /work?mode=read|write|mixed&size_kb=128&key=lab/test.bin"
        }
    })

@app.post("/text")
def write_text():
    body = request.get_json(force=True, silent=False)
    key = body.get("key")
    text = body.get("text", "")
    metadata = body.get("metadata")
    if not key:
        return jsonify({"error": "key is required"}), 400
    try:
        info = put_bytes(key, text.encode("utf-8"), content_type="text/plain; charset=utf-8", metadata=metadata)
        return jsonify({"ok": True, **info})
    except ClientError as e:
        log.exception("S3 put failed")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/text/<path:key>")
def read_text(key: str):
    version_id = request.args.get("versionId")
    try:
        info = get_bytes(key, version_id=version_id)
        data = info.pop("data")
        try:
            txt = data.decode("utf-8")
            info["text"] = txt
        except UnicodeDecodeError:
            info["note"] = "binary content not returned as text"
        return jsonify({"ok": True, **info})
    except ClientError as e:
        return jsonify({"ok": False, "error": str(e)}), 404

@app.get("/list")
def list_objects():
    prefix = request.args.get("prefix") or ""
    try:
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=1000)
        items = []
        for c in resp.get("Contents", []):
            items.append({"key": c["Key"], "size": c["Size"], "lastModified": c["LastModified"].isoformat()})
        return jsonify({"ok": True, "bucket": S3_BUCKET, "prefix": prefix, "items": items})
    except ClientError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/list-versions")
def list_versions():
    prefix = request.args.get("prefix") or ""
    try:
        resp = s3.list_object_versions(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=200)
        items = []
        for v in resp.get("Versions", []):
            items.append({
                "key": v["Key"], "versionId": v["VersionId"], "isLatest": v["IsLatest"],
                "size": v["Size"], "lastModified": v["LastModified"].isoformat()
            })
        for d in resp.get("DeleteMarkers", []):
            items.append({
                "key": d["Key"], "versionId": d["VersionId"], "isDeleteMarker": True,
                "isLatest": d["IsLatest"], "lastModified": d["LastModified"].isoformat()
            })
        return jsonify({"ok": True, "bucket": S3_BUCKET, "prefix": prefix, "versions": items})
    except ClientError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.delete("/object/<path:key>")
def delete_object(key: str):
    version_id = request.args.get("versionId")
    try:
        args = {"Bucket": S3_BUCKET, "Key": key}
        if version_id:
            args["VersionId"] = version_id
        resp = s3.delete_object(**args)
        return jsonify({"ok": True, "key": key, "versionId": resp.get("VersionId")})
    except ClientError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/work")
def work():
    """
    JMeter-friendly endpoint.
      mode: read | write | mixed (default mixed)
      size_kb: int (default 128, clamps 1..10240)
      key: base key (default lab/test.bin)
    """
    mode = (request.args.get("mode") or "mixed").lower()
    try:
        size_kb = int(request.args.get("size_kb", "128"))
    except ValueError:
        size_kb = 128
    size_kb = max(1, min(size_kb, 10240))
    key = request.args.get("key", "lab/test.bin")

    result = {"ok": True, "mode": mode, "size_kb": size_kb, "bucket": S3_BUCKET, "key": key}

    try:
        if mode in ("write", "mixed"):
            data = secrets.token_bytes(size_kb * 1024)
            versioned_key = f"{key}.{int(time.time()*1000)}"
            t1 = time.perf_counter()
            info_w = put_bytes(versioned_key, data)
            result["write"] = {"key": versioned_key, "versionId": info_w.get("versionId")}
            result["t_write_ms"] = int((time.perf_counter() - t1) * 1000)

        if mode in ("read", "mixed"):
            read_key = result["write"]["key"] if mode == "mixed" and "write" in result else key
            t2 = time.perf_counter()
            try:
                info_r = get_bytes(read_key)
                info_r.pop("data", None)
                result["read"] = {"key": read_key, "versionId": info_r.get("versionId"), "size": info_r.get("contentLength")}
            except ClientError as e:
                result["read_error"] = str(e)
            result["t_read_ms"] = int((time.perf_counter() - t2) * 1000)

        return jsonify(result)
    except ClientError as e:
        log.exception("S3 op failed")
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)