# components/deploy_kserve.py
import os, subprocess, tempfile, textwrap

ISVC_TEMPLATE = """\
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: {{MODEL_NAME}}
  namespace: {{NAMESPACE}}
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    sklearn:
      storageUri: {{MODEL_S3_URI}}
    serviceAccountName: {{SERVICE_ACCOUNT}}
  explainer:
    alibi:
      type: drift
      # minimal config; KServe pulls a default detector or you can point to a trained one in storageUri
      config:
        # example config key; replace with your desired Alibi detector config if needed
        threshold: 0.5
    serviceAccountName: {{SERVICE_ACCOUNT}}
"""

def render_isvc(model_name, namespace, model_s3_uri, service_account):
    y = ISVC_TEMPLATE
    y = y.replace("{{MODEL_NAME}}", model_name)
    y = y.replace("{{NAMESPACE}}", namespace)
    y = y.replace("{{MODEL_S3_URI}}", model_s3_uri)
    y = y.replace("{{SERVICE_ACCOUNT}}", service_account)
    return y

def deploy_isvc(model_name, namespace, model_s3_uri, service_account):
    yaml = render_isvc(model_name, namespace, model_s3_uri, service_account)
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(yaml)
        path = f.name
    try:
        subprocess.check_call(["kubectl","apply","-f", path])
    finally:
        os.unlink(path)

if __name__ == "__main__":
    deploy_isvc(
        model_name=os.environ["MODEL_NAME"],
        namespace=os.environ["SERVE_NAMESPACE"],
        model_s3_uri=os.environ["MODEL_S3_URI"],
        service_account=os.environ.get("SERVICE_ACCOUNT","default"),
    )
