# mcp-vision

## Overview
A Model Context Protocol (MCP) server for using HuggingFace computer vision models as tools for LLM use.

This MCP server is still in early development. The functionality and available tools are subject to change and expansion. 
See below for details of currently available tools.

## Tools
The following tools are currently available through the mcp-vision server:

1. **locate_objects**
- Description: Detect and locate objects in an image using one of the zero-shot object detection pipelines available 
through HuggingFace (list for reference [https://huggingface.co/models?pipeline_tag=zero-shot-object-detection&sort=trending]). 
- Input: `image_path` (string) URL or file path, `candidate_labels` (list of strings) list of possible objects to detect, `hf_model` (optional string), will use `"google/owlvit-large-patch14"` by default, which could be slow on a non-GPU machine
- Returns: List of dicts in HF object-detection format

2. **zoom_to_object**
- Description: Zoom into an object in the image, allowing you to analyze it more closely. Crop image to the object bounding box and return the cropped image. If many objects are present in the image, will return the 'best' one as represented by object score.
- Input: `image_path` (string) URL or file path, `label` (string) object label to find and zoom and crop to, `hf_model` (optional), will use `"google/owlvit-large-patch14"` by default, which could be slow on a non-GPU machine
- Returns: MCPImage or None

## Configuration

### Usage with Claude Desktop
Add this to your claude_desktop_config.json:

#### Docker
CPU only:
```json
"mcpServers": {
  "mcp-vision": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "mcp-vision"],
	"env": {}
  }
}
```
Or, alternatively, if your local environment has access to a NVIDIA GPU:
```json
"mcpServers": {
  "mcp-vision": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "--runtime=nvidia", "--gpus", "all", "mcp-vision"],
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
make run-docker-cpu
```
or 
```bash
make run-docker-gpu
```

[Groundlight Internal] Push the Docker image to Docker Hub (requires DockerHub credentials):
```bash
make push-docker
```


