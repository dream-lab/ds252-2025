FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir kfp==2.7.0 pandas pyarrow scikit-learn boto3 feast
# If you’ll read from S3 inside training:
RUN pip install --no-cache-dir s3fs
COPY train_component.py /app/train_component.py
ENTRYPOINT ["python", "/app/train_component.py"]
