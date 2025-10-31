# ecommerce_features/feature_repo/features.py
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Int64, Float32, String, ValueType

sales_source = FileSource(
    path="data/processed/sales.parquet",
    timestamp_field="event_timestamp",
)

# Be explicit to silence the deprecation warning
order = Entity(
    name="order_id",
    join_keys=["order_id"],
    value_type=ValueType.STRING,
)

sales_fv = FeatureView(
    name="sales_features",
    entities=[order],
    ttl=timedelta(days=5000),
    schema=[
        Field(name="category", dtype=String),
        Field(name="qty", dtype=Int64),
        Field(name="amount", dtype=Float32),
    ],
    online=True,
    source=sales_source,
)
