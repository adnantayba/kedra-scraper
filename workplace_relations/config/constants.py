"""
Project constants and configuration values.
"""

# Storage Configuration
STORAGE_BASE = "storage"
PROCESSED_STORAGE_BASE = "processed_storage"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017"
MONGO_DATABASE = "workplace_relations"
MONGO_LANDING_COLLECTION = "landing_zone"
MONGO_PROCESSED_COLLECTION = "processed_documents"

# MinIO Configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "documents"

# Scrapy Configuration
BOT_NAME = "workplace_relations"
SPIDER_MODULES = ["workplace_relations.spiders"]
NEWSPIDER_MODULE = "workplace_relations.spiders"

# Spider Configuration
MAX_DOCUMENTS = 1000
ALLOWED_DOMAINS = ["workplacerelations.ie"]
START_URL = "https://www.workplacerelations.ie/en/search/"

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

# Concurrency Settings
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1.5

# File Processing
SUPPORTED_FILE_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'html': 'text/html'
}

# Date Formats
DATE_FORMAT_INPUT = "%Y-%m-%d"
DATE_FORMAT_DISPLAY = "%d/%m/%Y"
DATE_FORMAT_PARTITION = "%Y-%m"

# Processing Configuration
PROCESSING_VERSION = "1.0" 