```markdown
# kedra-scraper

A professional, scalable web scraping pipeline for Workplace Relations Ireland legal documents.

## Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)

## Features
- **Modular, maintainable architecture** using Separation of Concerns and design patterns
- **Scrapy** for robust web crawling
- **Dagster** for orchestration and asset management
- **MongoDB** for document metadata storage
- **Centralized configuration and logging**
- **Easily extensible** for new pipelines, spiders, or storage backends

## Project Structure

```
workplace_relations/
├── config/           # Centralized config, constants, logging
├── core/             # Models, services, utils
├── pipelines/        # Modular pipelines (landing, processing)
├── repositories/     # Data access layer (abstract + Mongo)
├── spiders/          # Scrapy spiders (clean, config-driven)
├── dagster_assets.py # Dagster asset definitions (refactored)
├── items.py          # Scrapy compatibility only
├── middlewares.py    # Scrapy middlewares (centralized logging)
├── repository.py     # Dagster Definitions
├── resources.py      # Dagster Resources
├── settings.py       # Loads from centralized config
```

## Docker Setup

This project uses Docker to containerize the application and its dependencies:

- **MongoDB**: Running in a separate container (mongo:5.0)
- **kedra-scraper**: Application container with all Python dependencies
- **Storage Volumes**: 
  - Local `storage/` directory mapped to container for raw document storage
  - Local `processed_storage/` directory mapped to container for processed document storage
  - Local `config/` directory mapped to container for configuration

To stop the application:
```bash
docker-compose down
```

To rebuild the application after code changes:
```bash
docker-compose up --build
```

## Usage

### 1. Setup Project Directories
```bash
mkdir -p storage processed_storage
```

### 2. Start the Application with Docker
```bash
docker-compose up --build
```

### 3. Access the Application
- Dagster UI: [http://localhost:3000](http://localhost:3000)
- MongoDB: localhost:27017 (for direct connections)

### 4. Run an Asset
- Select the asset you want to run (e.g., `scrape_and_store_landing_zone` or `transform_landing_zone_documents`).
- Provide config in the UI, e.g.:

```yaml
ops:
  scrape_and_store_landing_zone:
    config:
      start_date: "2025-01-01"
      end_date: "2025-03-01"
      bodies: "labour court"  # Optional
```

```yaml
ops:
  transform_landing_zone_documents:
    config:
      start_date: "2025-01-01"
      end_date: "2025-03-01"
```

- Click "Launch Run".

### 5. Output
- Scraped documents are stored in MongoDB and files in the local `storage/` directory (mapped to container volume).
- Processed documents are stored in local `processed_storage/` directory and MongoDB.

## Architecture Overview
- **Config**: All settings, constants, and logging are centralized in `config/`.
- **Core**: Business logic, models, and utilities are in `core/`.
- **Pipelines**: Data processing is modularized in `pipelines/`.
- **Repositories**: Data access is abstracted and easily swappable.
- **Spiders**: Scrapy spiders are clean, config-driven, and focused only on crawling/extraction.
- **Dagster**: Orchestration and asset management are handled via Dagster assets and resources.

## Contributing

1. **Fork the repository** and clone your fork.
2. **Create storage directories**:
   ```bash
   mkdir -p storage processed_storage
   ```
3. **Start the application**:
   ```bash
   docker-compose up --build
   ```
4. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b my-feature
   ```
5. **Make your changes** following the project structure and code style.
6. **Test your changes** through the Dagster UI at http://localhost:3000
7. **Commit and push** your changes:
   ```bash
   git add .
   git commit -m "Describe your change"
   git push origin my-feature
   ```
8. **Open a Pull Request** on GitHub.

### Coding Guidelines
- Follow the existing modular structure and separation of concerns.
- Use centralized config and logging.
- Add docstrings and comments for clarity.
```