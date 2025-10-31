from kfp import Client
import os

ENDPOINT = os.environ.get("KFP_ENDPOINT", "http://<pipelines-endpoint>")  # or port-forward/ui proxy URL
c = Client(host=ENDPOINT)

run = c.create_run_from_pipeline_package(
    pipeline_file="pipeline.yaml",
    arguments={
        "input_parquet": "s3://ml-bucket-nikhil/data/sales.parquet",
        "model_s3_uri":  "s3://ml-bucket-nikhil/models/sales-model/model.joblib",
        "target":        "amount",
    },
    enable_caching=False,
)
print("Run created:", run.run_id)
