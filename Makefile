.PHONY: install-server build-docker run-docker push-docker

build-docker:  # Build the Docker image for the MCP vision server
	docker build -t mcp-vision .

run-docker-cpu: # Run the Docker container on CPU only
	docker run -it --rm mcp-vision

run-docker-gpu:  # Run the Docker container with NVIDIA GPU access
	docker run -it --rm --runtime=nvidia --gpus all mcp-vision

push-docker:  # Push the Docker image to the registry
	docker tag mcp-vision utarn/mcp-vision:latest
	docker push utarn/mcp-vision
