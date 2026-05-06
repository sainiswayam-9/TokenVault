# import_leads.py
# Imports ChattySalon.CSV into MongoDB as a new 'leads' collection in rbac_db.
# Usage: python import_leads.py
# Make sure MongoDB is running before executing.

import asyncio
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "rbac_db"
COLLECTION = "leads"
CSV_PATH = "ChattySalon.CSV"   # <-- put the CSV in the same folder, or use the full path


def clean_row(row: dict) -> dict:
    """Convert a pandas row to a clean MongoDB document."""
    return {
        "business_name":    row.get("Business Name") or None,
        "business_address": row.get("Business Address") or None,
        "business_phone":   row.get("Business Phone") or None,
        "business_website": row.get("Business Website") or None,
        "business_email":   row.get("Business Email") or None,
        "facebook":         row.get("Facebook") or None,
        "twitter":          row.get("Twitter") or None,
        "linkedin":         row.get("Linkedin") or None,
        "keyword":          row.get("Keyword") or None,
        "location":         row.get("Location") or None,
        "date_extracted":   row.get("Date Extracted") or None,
    }


async def import_leads():
    # Load CSV — treat empty strings as NaN so we can replace with None
    df = pd.read_csv(CSV_PATH, keep_default_na=True)
    df = df.where(pd.notnull(df), None)   # NaN → None (JSON-serializable)

    records = [clean_row(row) for row in df.to_dict(orient="records")]

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]

    # Drop existing collection for a clean import (remove this line to append instead)
    await db[COLLECTION].drop()
    print(f"Dropped existing '{COLLECTION}' collection.")

    result = await db[COLLECTION].insert_many(records)
    print(f"✓ Inserted {len(result.inserted_ids)} leads into '{DATABASE_NAME}.{COLLECTION}'")

    # Quick sanity check
    sample = await db[COLLECTION].find_one({})
    print("\nSample document:")
    for k, v in sample.items():
        if k != "_id":
            print(f"  {k}: {v}")

    client.close()
    print("\n✅ Import complete!")


if __name__ == "__main__":
    asyncio.run(import_leads())
