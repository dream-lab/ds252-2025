# components/drift_check_component.py
from kfp import dsl
from kfp.dsl import Output, Metrics
import json

@dsl.component(base_image="python:3.11")
def drift_check(
    drift_endpoint: str,
    s3_probe_path: str,
    region: str,
    threshold: float,
    out_metrics: Output[Metrics]
) -> bool:
    import boto3, requests, os, tempfile, json

    s3 = boto3.client("s3", region_name=region)
    if not s3_probe_path.startswith("s3://"):
        raise ValueError("s3_probe_path must be s3://bucket/key")
    bucket = s3_probe_path.replace("s3://","").split("/")[0]
    key    = "/".join(s3_probe_path.replace("s3://","").split("/")[1:])

    tmp = tempfile.NamedTemporaryFile(delete=False)
    s3.download_file(bucket, key, tmp.name)
    with open(tmp.name) as f:
        payload = json.load(f)

    # Payload must match your Alibi detector input schema
    # Example Alibi Detect v2 protocol:
    resp = requests.post(drift_endpoint, json=payload, timeout=30)
    resp.raise_for_status()
    r = resp.json()

    # Extract drift score / is_drift from response (adapt to your detector)
    # Common Alibi Detect v2: predictions-> [ { drift:..., p_value:..., is_drift: 0/1 } ]
    pred = r.get("outputs") or r.get("predictions") or r
    # Fallback heuristics:
    score = float(pred[0].get("drift", pred[0].get("p_value", 0.0)))
    is_drift = int(pred[0].get("is_drift", 1 if score > threshold else 0))

    out_metrics.log_metric("drift_score", score)
    out_metrics.log_metric("threshold", threshold)
    out_metrics.log_metric("is_drift", is_drift)

    return bool(is_drift == 1)
