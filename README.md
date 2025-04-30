# mcp-vision

## Overview
A Model Context Protocol (MCP) server for using HuggingFace computer vision models as tools for LLM use.

This MCP server is still in early development. The functionality and available tools are subject to change and expansion. 
See below for details of currently available tools.

## Tools
The following tools are currently available through the mcp-vision server:

1. **locate_objects**
- Description: Detect and locate objects in an image using one of the zero-shot object detection models available 
through HuggingFace (list for reference [https://huggingface.co/models?pipeline_tag=zero-shot-object-detection&sort=trending]). 
- Input: `image_path` (string) URL or file path, `candidate_labels` (list of strings) list of possible objects to detect, `hf_model` (optional string), will use `"google/owlvit-base-patch32"` by default
- Returns: List of dicts in HF object-detection format

## Configuration

### Usage with Claude Desktop
Add this to your claude_desktop_config.json:

#### Docker
```json
"mcpServers": {
  "mcp-vision": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "mcp-vision"],
	"env": {}
  }
}
```

## Development

Build the Docker image locally:
```bash
make build-docker
```

Run the Docker image locally:
```bash
make run-docker
```

[Groundlight Internal] Push the Docker image to Docker Hub (requires DockerHub credentials):
```bash
make push-docker
```


