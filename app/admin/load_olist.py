import pandas as pd
from sqlalchemy import text
from app.core.database import engine

BASE_PATH = "/app/datasets/olist/"  # Inside container path

files_in_order = [
    ("customers", "olist_customers_dataset.csv"),
    ("sellers", "olist_sellers_dataset.csv"),
    ("products", "olist_products_dataset.csv"),
    ("orders", "olist_orders_dataset.csv"),
    ("order_items", "olist_order_items_dataset.csv"),
    ("payments", "olist_order_payments_dataset.csv"),
    ("reviews", "olist_order_reviews_dataset.csv"),
    ("geolocation", "olist_geolocation_dataset.csv"),
]

print("🚀 Starting Olist Data Load...")

# Create schema safely
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS olist;"))

for table, file in files_in_order:
    print(f"📦 Loading {table}...")

    full_path = BASE_PATH + file

    # 🔥 SPECIAL HANDLING FOR LARGE FILE
    if table == "geolocation":
        print("⚡ Using chunked loading for geolocation (large file)...")
        
        first_chunk = True
        for chunk in pd.read_csv(full_path, chunksize=100000):
            chunk.to_sql(
                table,
                engine,
                schema="olist",
                if_exists="replace" if first_chunk else "append",
                index=False,
            )
            first_chunk = False
    else:
        df = pd.read_csv(full_path)
        df.to_sql(
            table,
            engine,
            schema="olist",
            if_exists="replace",
            index=False,
        )

print("✅ All Olist tables loaded successfully.")
