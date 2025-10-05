import logging
import os
import sys
from typing import Any
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from mcp_vision.server import mcp, init_ocr_reader

logger = logging.getLogger(__name__)

class ToolRequest(BaseModel):
    tool: str
    arguments: dict[str, Any]

class ToolResponse(BaseModel):
    content: list[dict[str, Any]]
    isError: bool = False

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting HTTP MCP-vision server...")
    try:
        # Initialize OCR reader
        init_ocr_reader()
        logger.info("MCP-vision HTTP server started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise e
    finally:
        logger.info("MCP-vision HTTP server shutting down")

app = FastAPI(
    title="MCP Vision Server",
    description="HTTP API for MCP Vision tools",
    version="0.1.1",
    lifespan=app_lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-vision"}

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    try:
        tools = []
        for tool_name, tool_info in mcp.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool_info.description,
                "inputSchema": tool_info.input_schema
            })
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/call/{tool_name}")
async def call_tool(tool_name: str, arguments: dict[str, Any]):
    """Call an MCP tool by name"""
    try:
        if tool_name not in mcp.tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Call the tool
        result = await mcp.tools[tool_name].run(**arguments)
        
        # Convert result to JSON-serializable format
        if hasattr(result, 'content'):
            content = [{"type": "text", "text": str(item)} for item in result.content]
        else:
            content = [{"type": "text", "text": str(result)}]
        
        return ToolResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        error_content = [{"type": "text", "text": f"Error: {str(e)}"}]
        return ToolResponse(content=error_content, isError=True)

@app.post("/invoke")
async def invoke_tool(request: ToolRequest):
    """Generic tool invocation endpoint"""
    return await call_tool(request.tool, request.arguments)

def main():
    """Entry point for HTTP server"""
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    
    uvicorn.run(
        "mcp_vision.http_server:app",
        host=host,
        port=port,
        reload=False,
        access_log=True
    )

if __name__ == "__main__":
    main()