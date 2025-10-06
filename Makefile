.PHONY: install-server build-docker run-docker push-docker docker-compose-up docker-compose-down docker-compose-logs

build-docker:  # Build the Docker image for the MCP vision server
	docker build -t mcp-vision .

run-docker-cpu: # Run the Docker container on CPU only
	docker run -it --rm mcp-vision

run-docker-gpu:  # Run the Docker container with NVIDIA GPU access
	docker run -it --rm --runtime=nvidia --gpus all mcp-vision

push-docker:  # Push the Docker image to the registry
	docker tag mcp-vision utarn/mcp-vision:latest
	docker push utarn/mcp-vision

docker-compose-up:  # Build and start services with Docker Compose (GPU enabled)
	docker-compose up --build

docker-compose-down:  # Stop and remove Docker Compose services
	docker-compose down

docker-compose-logs:  # View Docker Compose logs
	docker-compose logs -f

docker-compose-cpu:  # Start Docker Compose without GPU (CPU-only)
	docker-compose -f docker-compose.yml up --build
