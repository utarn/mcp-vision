# GPU Setup Guide for MCP Vision

This guide explains how to configure and use GPU acceleration with the MCP Vision server.

## Prerequisites

### NVIDIA Driver Installation
Before using GPU support, ensure you have the NVIDIA drivers installed on your host system:

```bash
# Check if NVIDIA drivers are installed
nvidia-smi

# If not installed, install drivers based on your OS
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y nvidia-driver-535

# Or download from NVIDIA website: https://www.nvidia.com/Download/index.aspx
```

### NVIDIA Container Toolkit
Install the NVIDIA Container Toolkit to enable GPU access in Docker containers:

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker daemon
sudo systemctl restart docker
```

## Usage

### Running with GPU Support

1. **Using Docker Compose (Recommended):**
   ```bash
   docker-compose up --build
   ```
   
   The `docker-compose.yml` file is already configured with GPU support.

2. **Using Docker directly:**
   ```bash
   docker build -t mcp-vision-gpu .
   docker run --gpus all -p 8083:8080 mcp-vision-gpu
   ```

### GPU Configuration Options

The Docker Compose file includes the following GPU configuration:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

You can modify this based on your needs:

- **Use all available GPUs:**
  ```yaml
  count: all
  ```

- **Use specific GPU count:**
  ```yaml
  count: 2  # Use 2 GPUs
  ```

- **Use specific GPU capabilities:**
  ```yaml
  capabilities: [gpu, utility, compute]  # Specify GPU capabilities
  ```

## Verification

### Check GPU Access in Container

After starting the container, verify GPU access:

```bash
# Check if GPU is accessible inside the container
docker exec -it mcp-vision-server nvidia-smi

# Check Python GPU libraries
docker exec -it mcp-vision-server python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Performance Comparison

You can test the performance difference between CPU and GPU processing:

```bash
# Test with CPU (disable GPU)
docker-compose run --rm --gpus 0 mcp-vision python -c "
import time
import numpy as np
import easyocr
reader = easyocr.Reader(['en', 'th'])
dummy_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
start = time.time()
result = reader.readtext(dummy_image)
print(f'CPU processing time: {time.time() - start:.2f}s')
"

# Test with GPU
docker-compose run --rm mcp-vision python -c "
import time
import numpy as np
import easyocr
reader = easyocr.Reader(['en', 'th'], gpu=True)
dummy_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
start = time.time()
result = reader.readtext(dummy_image)
print(f'GPU processing time: {time.time() - start:.2f}s')
"
```

## Troubleshooting

### Common Issues

1. **"CUDA out of memory" error:**
   - Reduce batch size in your application
   - Use a smaller GPU count in docker-compose.yml
   - Process smaller images

2. **"NVIDIA driver not found" error:**
   - Ensure NVIDIA drivers are properly installed
   - Restart the Docker daemon after installing nvidia-container-toolkit
   - Check `nvidia-smi` works on the host system

3. **"GPU not available in container" error:**
   - Verify nvidia-container-toolkit is installed
   - Check Docker daemon is running with NVIDIA runtime
   - Test with `docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi`

### Logs and Monitoring

Monitor GPU usage and container logs:

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# View container logs
docker-compose logs -f mcp-vision

# Check container resource usage
docker stats mcp-vision-server
```

## Environment Variables

You can customize GPU behavior with these environment variables in `docker-compose.yml`:

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Use specific GPU
  - NVIDIA_VISIBLE_DEVICES=all  # Use all GPUs
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility  # Specify driver capabilities
```

## Performance Tips

1. **Warm up GPU models:** The Dockerfile pre-downloads and warms up EasyOCR models during build time.

2. **Optimize batch processing:** Process multiple images in batches when possible to maximize GPU utilization.

3. **Monitor GPU memory:** Use `nvidia-smi` to monitor GPU memory usage and avoid OOM errors.

4. **Choose appropriate image sizes:** Very large images may cause GPU memory issues.

## Security Considerations

- The container needs access to NVIDIA drivers on the host system
- Ensure proper isolation when running in production environments
- Regularly update NVIDIA drivers and CUDA runtime for security patches