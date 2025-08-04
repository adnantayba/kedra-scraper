# dagster_assets.py
import os
from datetime import datetime
from typing import List, Dict, Optional

from dagster import asset, Output, MetadataValue, AssetExecutionContext
from pymongo import MongoClient
from bs4 import BeautifulSoup
import hashlib
import requests

# Configuration
MONGO_URI = "mongodb://localhost:27017"
LANDING_DB = "workplace_relations"
LANDING_COLLECTION = "landing_zone"
PROCESSED_DB = "workplace_relations"
PROCESSED_COLLECTION = "processed_documents"
STORAGE_BASE = "storage"
PROCESSED_STORAGE_BASE = "processed_storage"


@asset(required_resource_keys={"scrapy_runner"})
def scrape_and_store_landing_zone(context: AssetExecutionContext):
    config = context.op_config or {}
    result = context.resources.scrapy_runner.run_spider(
        spider_name="workplace",
        start_date=config.get("start_date", "2025-01-01"),
        end_date=config.get("end_date", "2025-12-31"),
        bodies=config.get("bodies", None),
    )

    # Verify results (optional)
    client = MongoClient(MONGO_URI)
    count = client[LANDING_DB][LANDING_COLLECTION].count_documents({})

    return Output(
        value={"document_count": count, "status": "completed"},
        metadata={"documents_in_db": count, "storage_path": os.path.abspath("storage")},
    )


@asset
def process_documents_from_landing_zone(
    context: AssetExecutionContext, scrape_and_store_landing_zone: dict
):
    """
    Asset that processes documents from the landing zone to the processed zone.
    """
    # Get the count from the dict
    document_count = scrape_and_store_landing_zone["document_count"]
    context.log.info(f"Processing {document_count} documents")

    client = MongoClient(MONGO_URI)
    landing_collection = client[LANDING_DB][LANDING_COLLECTION]

    # Debug: Log how many documents are found in MongoDB
    count = landing_collection.count_documents({})
    context.log.info(f"Found {count} documents in landing_zone")

    # Get date range from config or use defaults
    start_date = context.op_config.get("start_date", "2025-01-01")
    end_date = context.op_config.get("end_date", "2025-03-01")

    # Convert to datetime objects for MongoDB query
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    landing_db = client[LANDING_DB]
    landing_collection = landing_db[LANDING_COLLECTION]

    # Query documents in the date range
    query = {
        "published_date": {
            "$gte": start_dt.strftime("%d/%m/%Y"),
            "$lte": end_dt.strftime("%d/%m/%Y"),
        }
    }

    documents = list(landing_collection.find(query))
    processed_count = 0
    skipped_count = 0

    # Create processed storage directory if it doesn't exist
    os.makedirs(PROCESSED_STORAGE_BASE, exist_ok=True)

    # Process each document
    processed_docs = []
    for doc in documents:
        try:
            # Get file path from landing zone
            landing_path = doc["file_path"]
            file_type = doc["file_type"]
            identifier = doc["identifier"]

            # Read the file content
            with open(landing_path, "rb") as f:
                content = f.read()

            new_content = content
            new_hash = doc["file_hash"]

            # Process HTML files
            if file_type == "html":
                soup = BeautifulSoup(content, "html.parser")
                main_content = soup.find("div", {"class": "col-sm-9"})

                if main_content:
                    new_content = str(main_content).encode("utf-8")
                    new_hash = hashlib.sha256(new_content).hexdigest()

            # Create new file path with identifier as name
            new_filename = f"{identifier}.{file_type}"
            body_dir = doc["body"].replace(" ", "_")
            partition_dir = doc["partition_date"]

            new_path = os.path.join(
                PROCESSED_STORAGE_BASE, body_dir, partition_dir, new_filename
            )

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # Write the processed file
            with open(new_path, "wb") as f:
                f.write(new_content)

            # Create processed document metadata
            processed_doc = {
                "identifier": identifier,
                "description": doc["description"],
                "published_date": doc["published_date"],
                "partition_date": doc["partition_date"],
                "body": doc["body"],
                "original_link": doc["link_to_doc"],
                "file_type": file_type,
                "file_path": new_path,
                "file_hash": new_hash,
                "processed_at": datetime.now().isoformat(),
                "source_document_id": str(doc["_id"]),
            }

            processed_docs.append(processed_doc)
            processed_count += 1

        except Exception as e:
            context.log.error(
                f"Failed to process document {doc.get('identifier')}: {e}"
            )
            skipped_count += 1
            continue

    # Store processed documents in MongoDB
    if processed_docs:
        processed_db = client[PROCESSED_DB]
        processed_collection = processed_db[PROCESSED_COLLECTION]
        result = processed_collection.insert_many(processed_docs)

        context.log.info(f"Inserted {len(result.inserted_ids)} processed documents")

    # Close MongoDB connection
    client.close()

    # Prepare metadata for the asset
    metadata = {
        "documents_processed": processed_count,
        "documents_skipped": skipped_count,
        "start_date": start_date,
        "end_date": end_date,
    }

    return Output(value=processed_count, metadata=metadata)
