# kedra-scraper

A professional, scalable web scraping pipeline for Workplace Relations Ireland legal documents.

---

## Features
- **Modular, maintainable architecture** using Separation of Concerns and design patterns
- **Scrapy** for robust web crawling
- **Dagster** for orchestration and asset management
- **MongoDB** for document metadata storage
- **Centralized configuration and logging**
- **Easily extensible** for new pipelines, spiders, or storage backends

---

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

---

## Usage

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Dagster for Orchestration
```bash
dagster dev -m workplace_relations.repository
```

### 3. Open Dagster UI
Go to [http://localhost:3000](http://localhost:3000) in your browser.

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

ops:
  transform_landing_zone_documents:
    config:
      start_date: "2025-01-01"
      end_date: "2025-03-01"
```

- Click "Launch Run".

### 5. Output
- Scraped documents are stored in MongoDB and files in the `storage/` directory.
- Processed documents are stored in `processed_storage/` and MongoDB.

---

## Architecture Overview
- **Config:** All settings, constants, and logging are centralized in `config/`.
- **Core:** Business logic, models, and utilities are in `core/`.
- **Pipelines:** Data processing is modularized in `pipelines/`.
- **Repositories:** Data access is abstracted and easily swappable.
- **Spiders:** Scrapy spiders are clean, config-driven, and focused only on crawling/extraction.
- **Dagster:** Orchestration and asset management are handled via Dagster assets and resources.

---

## Contributing

1. **Fork the repository** and clone your fork.
2. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b my-feature
   ```
3. **Make your changes** following the project structure and code style.
5. **Commit and push** your changes:
   ```bash
   git add .
   git commit -m "Describe your change"
   git push origin my-feature
   ```
6. **Open a Pull Request** on GitHub.

### Coding Guidelines
- Follow the existing modular structure and separation of concerns.
- Use centralized config and logging.
- Add docstrings and comments for clarity.
