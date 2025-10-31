# pipelines/retrain_pipeline.py
from kfp import dsl
from kfp import compiler
from kfp.dsl import Input, Output, Metrics, Model, Condition, component

# Load the drift component from source file
from kfp.components import load_component_from_file
drift_check_op = load_component_from_file("components/drift_check_component.py")

# Load the train container component spec and bind image at runtime
from kfp.components import load_component_from_text
train_spec_text = open("components/train_component.yaml").read()

@dsl.component
def passthrough_bool(flag: bool) -> bool:
    return flag

@dsl.pipeline(
    name="ecommerce-retrain-pipeline",
    description="Check drift, then retrain if drift > threshold"
)
def ecommerce_retrain_pipeline(
    drift_endpoint: str,
    s3_probe_path: str,
    s3_input: str,
    s3_model_dir: str,
    region: str = "ap-south-1",
    threshold: float = 0.5,
    train_image: str = "REPLACEME"
):
    drift_task = drift_check_op(
        drift_endpoint=drift_endpoint,
        s3_probe_path=s3_probe_path,
        region=region,
        threshold=threshold
    )

    # Bring the returned bool into a pure bool output for the when-condition
    flag = passthrough_bool(flag=drift_task.output)

    # Bind the train image to the component spec
    train_component = load_component_from_text(
        train_spec_text.replace("{{ .inputs.train_image }}", train_image)
    )

    with dsl.If(flag.output == True):   # only when drift detected
        train_component(
            s3_input=s3_input,
            s3_model_dir=s3_model_dir,
            region=region
        )

if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=ecommerce_retrain_pipeline,
        package_path="retrain_pipeline.json"
    )
