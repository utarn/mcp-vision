# Running MCP Vision Server Locally

This guide explains how to run the MCP vision server locally without Docker.

## Prerequisites

1. Python 3.11 or higher
2. UV package manager (recommended) or pip
3. Required system dependencies for EasyOCR (will be installed automatically)

## Setup Instructions

### Option 1: Using UV (Recommended)

1. Install UV if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   cd /Users/utarn/projects/mcp-vision
   uv sync
   ```

3. Run the server:
   ```bash
   uv run mcp-vision
   ```

### Option 2: Using pip

1. Create a virtual environment:
   ```bash
   cd /Users/utarn/projects/mcp-vision
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Run the server:
   ```bash
   python -m mcp_vision.server
   ```

## MCP Configuration

The `.roo/mcp.json` file has been updated to run the server locally using UV:

```json
{
  "mcpServers": {
    "mcp-vision": {
      "command": "uv",
      "args": [
        "run",
        "mcp-vision"
      ],
      "cwd": "/Users/utarn/projects/mcp-vision",
      "alwaysAllow": [
        "read_text_from_pdf"
      ],
      "timeout": 3600
    }
  }
}
```

## Testing the Server

You can test the server by running the test script:

```bash
uv run python test_runner.py
```

Or use pytest:

```bash
uv run pytest tests/
```

## Available Tools

The MCP vision server provides the following tools:

1. `read_text_from_image` - Extract text from images using EasyOCR
2. `read_text_from_pdf` - Extract text from PDF files by converting pages to images

Both tools support multiple languages including English and Thai, with confidence filtering options.

## Troubleshooting

1. **EasyOCR model download**: The first run will download OCR models, which may take a few minutes.
2. **Memory usage**: OCR processing can be memory-intensive, especially for large PDFs.
3. **Dependencies**: If you encounter issues with system dependencies, ensure you have the required libraries for image processing installed.

## Notes

- The server is configured to use stdio transport for MCP communication
- The timeout is set to 3600 seconds (1 hour) for PDF processing
- The server supports both local file paths and URLs for image/PDF processing