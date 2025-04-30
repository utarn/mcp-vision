.PHONY: install-server build-docker run-docker push-docker

build-docker:  # Build the Docker image for the MCP vision server
	docker build -t mcp-vision .

run-docker:  # Run the Docker container
	docker run -it --rm mcp-vision

push-docker:  # Push the Docker image to the registry
	docker tag mcp-vision groundlight/mcp-vision:latest
	docker push groundlight/mcp-vision
