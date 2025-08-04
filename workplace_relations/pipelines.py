# pipelines.py
import os
import hashlib
from urllib.parse import urlparse
from itemadapter import ItemAdapter
from pymongo import MongoClient
from workplace_relations.utils.logger import get_logger
import requests
from bs4 import BeautifulSoup

logger = get_logger(__name__)


class WorkplaceRelationsPipeline:
    def __init__(self):
        self.storage_base = "storage"  # Base directory for file storage
        os.makedirs(self.storage_base, exist_ok=True)

    def open_spider(self, spider):
        """Connect to MongoDB when spider opens"""
        try:
            self.client = MongoClient("mongodb://localhost:27017/")
            self.db = self.client["workplace_relations"]
            self.collection = self.db["landing_zone"]
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def close_spider(self, spider):
        """Close MongoDB connection when spider closes"""
        try:
            self.client.close()
            logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")

    def process_item(self, item, spider):
        spider.logger.info(f"Processing item: {item['identifier']}")

        try:
            item_dict = ItemAdapter(item).asdict()
            link = item_dict.get("link_to_doc")

            if link:
                spider.logger.debug(f"Downloading {link}")
                file_info = self.download_and_store_file(
                    link,
                    self.sanitize_filename(item_dict["body"]),
                    item_dict["partition_date"],
                )
                if file_info:
                    item_dict.update(file_info)

            # MongoDB insertion
            result = self.collection.insert_one(item_dict)
            spider.logger.info(
                f"Inserted {item['identifier']} (ID: {result.inserted_id})"
            )

            return item
        except Exception as e:
            spider.logger.error(
                f"Failed on {item['identifier']}: {str(e)}", exc_info=True
            )
            raise

    def sanitize_filename(self, name):
        """Convert string to safe filename"""
        keepchars = (" ", ".", "_", "-")
        return "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()

    def download_and_store_file(self, url, body_dir, partition_dir):
        """Download file from URL and store it in organized structure"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Determine file type from URL or content
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            if path.endswith(".pdf"):
                file_ext = "pdf"
                content = response.content
            elif path.endswith(".doc") or path.endswith(".docx"):
                file_ext = "docx" if path.endswith(".docx") else "doc"
                content = response.content
            else:
                # Assume HTML content
                file_ext = "html"
                soup = BeautifulSoup(response.text, "html.parser")
                content = str(soup).encode("utf-8")

            # Generate file hash
            file_hash = hashlib.sha256(content).hexdigest()

            # Create organized storage path
            storage_path = os.path.join(self.storage_base, body_dir, partition_dir)
            os.makedirs(storage_path, exist_ok=True)

            # Create filename with original name if possible
            original_name = os.path.splitext(os.path.basename(parsed_url.path))[0]
            safe_name = self.sanitize_filename(original_name)[:100]  # Limit length
            file_name = f"{safe_name}_{file_hash[:8]}.{file_ext}"
            file_path = os.path.join(storage_path, file_name)

            # Save file
            with open(file_path, "wb") as f:
                f.write(content)

            return {
                "file_path": file_path,
                "file_hash": file_hash,
                "file_type": file_ext,
            }

        except Exception as e:
            logger.error(f"Failed to download and store file {url}: {e}")
            return None
