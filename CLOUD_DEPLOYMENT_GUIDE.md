# Cloud Deployment Guide for MCP Vision Server

This guide explains how to deploy the MCP Vision server to your own cloud infrastructure and configure clients to connect to it remotely.

## Overview

The MCP Vision server can be deployed in two modes:
1. **Local (stdio)**: For development and local use
2. **Remote (HTTP)**: For cloud deployment and remote access

This guide focuses on the remote HTTP deployment.

## Prerequisites

- Docker and Docker Compose installed
- Cloud server or VM with Docker support
- (Optional) SSL certificates for HTTPS
- Domain name pointing to your server (recommended)

## Quick Start

### 1. Build and Deploy

```bash
# Clone the repository
git clone <your-repo-url>
cd mcp-vision

# Build and start the HTTP server
docker-compose up -d

# Check if the server is running
curl http://localhost:8080/health
```

### 2. Configure Client

Update your MCP client configuration to use the remote server:

```json
{
  "mcpServers": {
    "mcp-vision": {
      "type": "remote",
      "url": "https://your-server.com",
      "alwaysAllow": [
        "read_text_from_image",
        "read_text_from_pdf"
      ],
      "timeout": 3600
    }
  }
}
```

Replace `https://your-server.com` with your actual server URL.

## Deployment Options

### Option 1: Basic HTTP Deployment

For simple deployments without SSL:

```bash
# Deploy with basic HTTP
docker-compose up -d mcp-vision

# Access at: http://your-server:8080
```

### Option 2: HTTPS with Nginx

For production deployments with SSL:

```bash
# Create SSL directory
mkdir -p ssl

# Place your SSL certificates
# ssl/cert.pem - Your SSL certificate
# ssl/key.pem - Your private key

# Deploy with nginx
docker-compose --profile with-nginx up -d

# Access at: https://your-server.com
```

### Option 3: Custom Configuration

You can customize the deployment by modifying environment variables:

```yaml
# In docker-compose.yml
environment:
  - PORT=8080
  - HOST=0.0.0.0
```

## API Endpoints

The HTTP server provides the following endpoints:

### Health Check
```
GET /health
```

### List Available Tools
```
GET /tools
```

### Call Tool by Name
```
POST /call/{tool_name}
Content-Type: application/json

{
  "arg1": "value1",
  "arg2": "value2"
}
```

### Generic Tool Invocation
```
POST /invoke
Content-Type: application/json

{
  "tool": "read_text_from_image",
  "arguments": {
    "image_path": "https://example.com/image.jpg",
    "min_confidence": 0.5
  }
}
```

## Security Considerations

### Authentication (Optional)

For production deployments, consider adding authentication:

1. **API Key Authentication**: Add API key validation middleware
2. **OAuth**: Implement OAuth for secure access
3. **IP Whitelisting**: Restrict access to specific IP addresses

### SSL/TLS

Always use HTTPS in production:
- Obtain SSL certificates from Let's Encrypt or your CA
- Configure nginx for SSL termination
- Redirect HTTP to HTTPS

### Firewall

Configure your firewall to:
- Allow inbound traffic on ports 80 and 443
- Restrict access to the Docker container port (8080)

## Monitoring and Logging

### Health Checks

The server includes built-in health checks:
```bash
# Check container health
docker ps

# Manual health check
curl http://localhost:8080/health
```

### Logs

View application logs:
```bash
# View container logs
docker-compose logs -f mcp-vision

# View nginx logs (if using nginx)
docker-compose logs -f nginx
```

## Scaling and Performance

### Horizontal Scaling

For high-traffic deployments:
1. Use a load balancer
2. Deploy multiple instances
3. Configure session affinity if needed

### Resource Optimization

- **Memory**: EasyOCR models require significant RAM (2GB+ recommended)
- **CPU**: OCR is CPU-intensive, consider using faster CPUs
- **Storage**: Cache models locally to avoid re-downloading

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure port 8080 is available
2. **SSL errors**: Verify certificate paths and permissions
3. **OCR failures**: Check memory and disk space
4. **Timeout errors**: Increase timeout for large PDFs

### Debug Mode

Enable debug logging:
```yaml
environment:
  - LOG_LEVEL=DEBUG
```

### Performance Testing

Test the server performance:
```bash
# Test with a sample image
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "read_text_from_image",
    "arguments": {
      "image_path": "https://example.com/test.jpg"
    }
  }'
```

## Migration from Local to Remote

To migrate from local stdio to remote HTTP:

1. **Backup current configuration**
2. **Deploy the HTTP server** using this guide
3. **Update client configuration** to use `"type": "remote"`
4. **Test the connection** with a simple request
5. **Remove local configuration** once verified

## Example Configurations

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mcp-vision-cloud": {
      "type": "remote",
      "url": "https://mcp-vision.yourdomain.com",
      "alwaysAllow": [
        "read_text_from_image",
        "read_text_from_pdf"
      ],
      "timeout": 3600
    }
  }
}
```

### Custom Client Configuration

For custom MCP clients, use the HTTP endpoints directly:

```javascript
// Example client code
const response = await fetch('https://your-server.com/invoke', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'read_text_from_image',
    arguments: {
      image_path: 'https://example.com/document.jpg'
    }
  })
});

const result = await response.json();
console.log(result.content);
```

## Support

For issues and questions:
1. Check the application logs
2. Verify network connectivity
3. Test with the provided examples
4. Review the troubleshooting section above