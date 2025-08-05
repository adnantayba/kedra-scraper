# Workplace Relations Scraper Documentation

## Project Overview

The Workplace Relations Scraper is a comprehensive solution designed to extract, process, and store workplace relations documents from the official Irish website (workplacerelations.ie). This system implements a robust architecture that handles the complete document lifecycle from initial scraping through final processing and storage.

## Solution Architecture

The system follows a modular architecture with clear separation of concerns:

1. **Scraping Layer**: Responsible for crawling the website and extracting document metadata and content
2. **Processing Layer**: Handles document transformation and enrichment
3. **Storage Layer**: Manages document persistence in both raw and processed formats
4. **Monitoring Layer**: Tracks system performance and document processing metrics

## Key Features Implemented

### 1. Document Scraping and Collection

- **Targeted Crawling**: The spider specifically targets workplace relations documents while respecting robots.txt rules
- **Date Range Filtering**: Supports scraping documents within specific date ranges
- **Body Filtering**: Can filter documents by specific decision-making bodies
- **Pagination Handling**: Automatically follows pagination links to collect complete results
- **File Type Detection**: Identifies and handles different document formats (PDF, DOC, HTML)

### 2. Document Processing Pipeline

- **Landing Zone Storage**: Raw documents are initially stored with metadata in a landing zone
- **Content Processing**: Documents undergo transformation (HTML content extraction, etc.)
- **Duplicate Handling**: Identifies and manages duplicate documents
- **Metadata Enrichment**: Adds processing timestamps and version information
- **File Organization**: Stores processed documents in a structured directory hierarchy

### 3. Data Storage and Management

- **MongoDB Integration**: Uses MongoDB for document metadata storage
- **File System Storage**: Stores actual document files in organized directory structures
- **Dual Storage Areas**: Maintains separate landing and processed storage zones
- **Document Versioning**: Tracks original and processed versions of documents

### 4. Monitoring and Metrics

- **Performance Tracking**: Monitors memory and CPU usage during scraping
- **Document Statistics**: Tracks processed/failed documents and success rates
- **Processing Metrics**: Records processing speed and efficiency
- **Error Handling**: Logs and tracks processing failures

## Implementation Details

### Document Lifecycle

1. **Initial Scraping**:
   - Documents are identified through targeted crawling
   - Metadata is extracted including identifier, description, and publication date
   - Documents are downloaded and stored in the landing zone

2. **Landing Zone Storage**:
   - Raw documents are stored with initial metadata
   - File hashes are calculated for integrity verification
   - Documents await processing in the landing zone

3. **Processing Phase**:
   - Documents are transformed based on their file type
   - HTML content is extracted and cleaned
   - Processed versions are created and stored separately
   - Metadata is updated with processing information

4. **Processed Storage**:
   - Final versions of documents are stored in the processed zone
   - Relationships to original documents are maintained
   - Processing version information is added

### Data Model

The system uses a comprehensive document model that includes:

- Core identification fields (identifier, description)
- Temporal information (published date, partition date)
- Source information (link, body)
- Storage details (file paths, hashes)
- Processing metadata (timestamps, version)

## Matching with Requirements

The implementation fully addresses the requirements outlined in the project specification:

1. **Scraping Functionality**:
   - Implements all specified scraping capabilities
   - Handles date ranges and body filtering as required
   - Respects website policies and limitations

2. **Processing Requirements**:
   - Provides complete document processing pipeline
   - Implements content transformation for different file types
   - Includes duplicate detection and handling

3. **Storage Solution**:
   - Uses MongoDB as specified for metadata storage
   - Implements the dual-zone storage architecture
   - Maintains relationships between original and processed documents

4. **Additional Features**:
   - Includes comprehensive monitoring and metrics
   - Provides detailed logging throughout the process
   - Implements robust error handling

## Sample Data Output

The system produces structured output in both MongoDB collections and the file system:

**Landing Zone Document**:
- Contains initial document metadata
- Stores raw document content
- Includes file hash for verification
- Marks documents as unprocessed

**Processed Document**:
- Contains enriched metadata
- Stores transformed document content
- References original document
- Includes processing version information

## Conclusion

This solution provides a complete, production-ready system for scraping and processing workplace relations documents. The implementation follows software engineering best practices with clear separation of concerns, comprehensive error handling, and detailed monitoring capabilities. The system is designed for reliability and maintainability while meeting all specified requirements.