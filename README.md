# AI OCR Assist

OCR service for processing orders and invoices with Japanese language support.

## API Endpoints

### Parse Orders
```http
POST /api/v1/orders/parse
```
Parse CSV or Excel order files.
- File size limit: 1MB
- Supported formats: CSV, XLSX

### Parse Invoices
```http
POST /api/v1/invoices/parse
```
Parse PDF invoices with optional OCR support.
- File size limit: 1MB
- OCR support for Japanese text
- Parameter: use_ocr (boolean)

### Match Documents
```http
POST /api/v1/match
```
Match orders with invoices.
- File size limit: 1MB per file
- Requires both order file and invoice PDF

## Development Setup

1. Install Docker and Docker Compose
2. Clone the repository
3. Create `.env` file with required environment variables:
   ```
   OPENAI_API_KEY=your_api_key
   ```
4. Start the services:
   ```bash
   docker-compose up -d
   ```

## Testing
Access the API documentation at http://localhost:8000/docs
