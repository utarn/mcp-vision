# MCP Vision HTTP Server Setup

This document explains how to run the MCP Vision server as a local web server and connect to it via remote MCP HTTP.

## Running the HTTP Server

The HTTP server is already running on port 8080. To start it manually:

```bash
uv run python -m mcp_vision.http_server
```

The server will:
- Listen on `0.0.0.0:8080` (accessible from localhost)
- Initialize EasyOCR with English and Thai language support
- Provide REST API endpoints for the vision tools

## MCP Configuration

The `.roo/mcp.json` file is already configured to connect via remote HTTP:

```json
{
  "mcpServers": {
    "mcp-vision": {
      "type": "remote",
      "url": "http://localhost:8080",
      "alwaysAllow": [
        "read_text_from_pdf",
        "read_text_from_image"
      ],
      "timeout": 3600
    }
  }
}
```

### Configuration Details:
- **type**: `remote` - Uses HTTP/SSE transport instead of stdio
- **url**: `http://localhost:8080` - Server endpoint
- **alwaysAllow**: Pre-approved tools that don't require user confirmation
- **timeout**: 3600 seconds (1 hour) for long-running operations

## Available Endpoints

### 1. Health Check
```bash
GET http://localhost:8080/health
```
Returns server status.

### 2. List Tools
```bash
GET http://localhost:8080/tools
```
Returns available MCP tools with their schemas.

### 3. Call Tool
```bash
POST http://localhost:8080/call/{tool_name}
Content-Type: application/json

{
  "param1": "value1",
  "param2": "value2"
}
```

### 4. Generic Invoke
```bash
POST http://localhost:8080/invoke
Content-Type: application/json

{
  "tool": "tool_name",
  "arguments": {
    "param1": "value1"
  }
}
```

## Testing the Server

Run the test script to verify all functionality:

```bash
uv run python test_http_mcp.py
```

This will test:
1. Health endpoint
2. Tools listing
3. Tool invocation with sample image

## Available Tools

1. **read_text_from_image**
   - Extract text from images using EasyOCR
   - Supports multiple languages
   - Configurable confidence threshold

2. **read_text_from_pdf**
   - Extract text from PDF files
   - Converts pages to images for OCR
   - Processes specified number of pages or all pages

## Example Usage

### Using curl:

```bash
# Health check
curl http://localhost:8080/health

# List tools
curl http://localhost:8080/tools

# Call read_text_from_image
curl -X POST http://localhost:8080/call/read_text_from_image \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "images/sample.png",
    "min_confidence": 0.0
  }'
```

### Using Python:

```python
import requests

# Call tool
response = requests.post(
    "http://localhost:8080/call/read_text_from_image",
    json={
        "image_path": "images/sample.png",
        "min_confidence": 0.0
    }
)

result = response.json()
if not result.get("isError"):
    text = result["content"][0]["text"]
    print(text)
```

## Troubleshooting

### Port Already in Use
If port 8080 is occupied:
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use a different port
PORT=8081 uv run python -m mcp_vision.http_server
```
Then update the URL in `.roo/mcp.json` accordingly.

### Connection Refused
Ensure:
1. Server is running (`uv run python -m mcp_vision.http_server`)
2. No firewall blocking port 8080
3. Using correct URL in configuration

### OCR Not Working
The server needs to download EasyOCR models on first run:
- English model: ~140MB
- Thai model: ~200MB
- This happens automatically but requires internet connection

## Production Deployment

For production use, consider:
1. Using a proper WSGI server (already uses uvicorn)
2. Adding authentication
3. Configuring CORS appropriately
4. Using HTTPS
5. Setting up proper logging
6. Adding rate limiting

See `CLOUD_DEPLOYMENT_GUIDE.md` for deployment instructions.