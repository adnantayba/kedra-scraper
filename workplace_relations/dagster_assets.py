# dagster_assets.py
import os

from dagster import asset, Output, OpExecutionContext
from pymongo import MongoClient


# Configuration
MONGO_URI = "mongodb://localhost:27017"
LANDING_DB = "workplace_relations"
LANDING_COLLECTION = "landing_zone"
PROCESSED_DB = "workplace_relations"
PROCESSED_COLLECTION = "processed_documents"
STORAGE_BASE = "storage"
PROCESSED_STORAGE_BASE = "processed_storage"


@asset(required_resource_keys={"scrapy_runner"})
def scrape_and_store_landing_zone(context: OpExecutionContext):
    config = context.op_config or {}
    result = context.resources.scrapy_runner.run_spider(
        spider_name="workplace",
        start_date=config.get("start_date"),
        end_date=config.get("end_date"),
        bodies=config.get("bodies"),
    )

    # Verify results (optional)
    client = MongoClient(MONGO_URI)
    count = client[LANDING_DB][LANDING_COLLECTION].count_documents({})

    return Output(
        value={"document_count": count, "status": "completed"},
        metadata={"documents_in_db": count, "storage_path": os.path.abspath("storage")},
    )


# dagster_assets.py (updated)
import os
from datetime import datetime

from dagster import asset, Output, OpExecutionContext
from pymongo import MongoClient
from bs4 import BeautifulSoup
import hashlib

# Configuration (add these to existing config)
PROCESSED_STORAGE_BASE = "processed_storage"
PROCESSED_COLLECTION = "processed_documents"


@asset(
    required_resource_keys={"mongo"},
    description="Transforms landing zone documents and stores them in processed location",
)
def transform_landing_zone_documents(context: OpExecutionContext):
    config = context.op_config or {}
    start_date = config.get("start_date")
    end_date = config.get("end_date")

    def convert_date_format(date_str):
        """Convert date string to DD/MM/YYYY format used in documents"""
        try:
            # Try parsing as YYYY-MM-DD first (config input format)
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            try:
                # Try parsing as MM-DD-YYYY (current config format)
                dt = datetime.strptime(date_str, "%m-%d-%Y")
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                # If already in correct format, return as-is
                if len(date_str) == 10 and date_str[2] == "/" and date_str[5] == "/":
                    return date_str
                raise ValueError(f"Unrecognized date format: {date_str}")

    # Initialize MongoDB client
    mongo_client = context.resources.mongo

    try:
        # 1. Fetch metadata from MongoDB landing zone
        landing_db = mongo_client[LANDING_DB]
        landing_collection = landing_db[LANDING_COLLECTION]

        # Convert query dates
        query_start = convert_date_format(start_date)
        query_end = convert_date_format(end_date)

        context.log.info(f"Looking for documents between {query_start} and {query_end}")

        # Debug: Print collection stats
        context.log.info(f"Collection stats: {landing_collection.count_documents({})}")
        context.log.info(f"Looking for documents between {start_date} and {end_date}")

        processed_collection = landing_db[PROCESSED_COLLECTION]
        # Add this debug code to your asset before the query:
        sample_doc = landing_collection.find_one({}, {"published_date": 1})
        context.log.info(
            f"Sample document date format: {sample_doc.get('published_date')}"
        )
        # Convert document dates during query using $expr
        query = {
            "$expr": {
                "$and": [
                    {
                        "$gte": [
                            {
                                "$dateFromString": {
                                    "dateString": "$published_date",
                                    "format": "%d/%m/%Y",
                                }
                            },
                            datetime.strptime(start_date, "%Y-%m-%d"),
                        ]
                    },
                    {
                        "$lte": [
                            {
                                "$dateFromString": {
                                    "dateString": "$published_date",
                                    "format": "%d/%m/%Y",
                                }
                            },
                            datetime.strptime(end_date, "%Y-%m-%d"),
                        ]
                    },
                ]
            }
        }
        # Debug: Print the query being executed
        context.log.info(f"Executing query: {query}")

        documents = list(landing_collection.find(query))
        context.log.info(f"Found {len(documents)} documents to process")

        processed_docs = []

        for doc in documents:
            try:
                file_path = doc.get("file_path")
                if not file_path or not os.path.exists(file_path):
                    context.log.warning(f"File not found: {file_path}")
                    continue

                # 2. Process each file based on type
                file_type = doc.get("file_type", "").lower()
                new_file_content = None

                if file_type == "html":
                    # 2.i. Process HTML files
                    with open(file_path, "r", encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")

                    # Extract relevant content (adjust xpath as needed)
                    content_div = soup.find("div", {"class": "col-sm-9"})
                    if not content_div:
                        content_div = soup.find("body") or soup

                    new_file_content = str(content_div).encode("utf-8")
                else:
                    # 2.ii. For PDF/DOC files, just read the content
                    with open(file_path, "rb") as f:
                        new_file_content = f.read()

                # 3. Calculate new hash
                new_file_hash = hashlib.sha256(new_file_content).hexdigest()

                # 4. Create new filename from identifier
                identifier = doc.get("identifier", "document")
                safe_identifier = "".join(
                    c if c.isalnum() else "_" for c in identifier
                )[
                    :100
                ]  # Limit length
                new_filename = f"{safe_identifier}.{file_type}"

                # 5. Create new storage path
                new_storage_path = os.path.join(
                    PROCESSED_STORAGE_BASE,
                    doc.get("body", "unknown"),
                    doc.get("partition_date", "unknown"),
                )
                os.makedirs(new_storage_path, exist_ok=True)
                new_file_path = os.path.join(new_storage_path, new_filename)

                # 6. Save processed file
                with open(new_file_path, "wb") as f:
                    f.write(new_file_content)

                # 7. Create new metadata document
                processed_doc = {
                    **doc,
                    "original_file_path": file_path,
                    "file_path": new_file_path,
                    "file_hash": new_file_hash,
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_version": "1.0",
                }

                # Remove internal fields if present
                for field in [
                    "depth",
                    "download_timeout",
                    "download_slot",
                    "download_latency",
                ]:
                    processed_doc.pop(field, None)

                processed_docs.append(processed_doc)

            except Exception as e:
                context.log.error(
                    f"Failed to process document {doc.get('identifier')}: {str(e)}"
                )
                continue

        # 8. Store processed metadata in new collection
        if processed_docs:
            result = processed_collection.insert_many(processed_docs)
            context.log.info(f"Inserted {len(result.inserted_ids)} processed documents")

        return Output(
            value={
                "processed_count": len(processed_docs),
                "start_date": start_date,
                "end_date": end_date,
            },
            metadata={
                "processed_documents": len(processed_docs),
                "processed_storage_path": os.path.abspath(PROCESSED_STORAGE_BASE),
                "mongo_collection": PROCESSED_COLLECTION,
            },
        )

    except Exception as e:
        context.log.error(f"Transform process failed: {str(e)}")
        raise
