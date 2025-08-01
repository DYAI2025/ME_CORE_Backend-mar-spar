# Docker Deployment Guide for MarkerEngine Core API

This guide covers deploying the MarkerEngine Core API using Docker, with special focus on Python-only deployment (no Java/Spark dependencies).

## 🚀 Quick Start

### 1. Build and Test Locally

```bash
# Make the build script executable
chmod +x docker-build.sh

# Build and test the production image
./docker-build.sh

# Or build manually
docker build --target base -t markerengine-core:latest .
```

### 2. Run Locally

```bash
# Run the production container
docker run -p 8000:8000 markerengine-core:latest

# Test the API
curl http://localhost:8000/health
```

## 🎯 Production Deployment

### Docker Stages Explained

This Dockerfile uses multi-stage build with two targets:

1. **`base` stage (Default/Production)**
   - Python 3.10 slim image
   - No Java dependencies
   - Minimal resource usage
   - Fast startup time
   - Perfect for Fly.io and similar platforms

2. **`spark` stage (Optional)**
   - Includes Java 11 and Spark NLP support
   - Larger image size
   - Higher resource requirements
   - Use only if you need NLP features

### Build Specific Stages

```bash
# Production build (Python-only, recommended)
docker build --target base -t markerengine-core:latest .

# Spark build (includes Java, larger image)
docker build --target spark -t markerengine-core:spark .

# Build for specific platform (useful for ARM64 Macs deploying to x86)
docker build --platform linux/amd64 --target base -t markerengine-core:latest .
```

## 🌍 Platform-Specific Deployment

### Fly.io Deployment

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and Initialize**
   ```bash
   flyctl auth login
   cd backend
   flyctl launch
   ```

3. **Deploy**
   ```bash
   flyctl deploy
   ```

4. **Set Environment Variables**
   ```bash
   # Set database connection (if needed)
   flyctl secrets set DATABASE_URL="mongodb://your-connection-string"
   
   # Set other environment variables
   flyctl secrets set ENVIRONMENT="production"
   ```

### Railway Deployment

```bash
# Connect to Railway
railway login
railway link

# Deploy
railway up
```

### Render Deployment

1. Connect your GitHub repository
2. Choose "Web Service"
3. Set build command: `docker build --target base -t markerengine .`
4. Set start command: `python minimal_app.py`

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Host to bind the server |
| `API_PORT` | `8000` | Port to listen on |
| `PYTHONUNBUFFERED` | `1` | Prevent Python buffering |
| `SPARK_NLP_ENABLED` | `false` | Enable/disable Spark NLP |
| `ENVIRONMENT` | `production` | Environment mode |
| `DATABASE_URL` | - | MongoDB connection string |

### Health Checks

The application provides multiple health check endpoints:

- `/health` - Main health endpoint
- `/api/health` - API health endpoint
- `/api/health/live` - Liveness probe
- `/api/health/ready` - Readiness probe
- `/healthz` - Kubernetes-style health check

## 🐛 Troubleshooting

### Common Issues

1. **"Java not found" errors**
   - Solution: Make sure you're using the `base` stage, not `spark`
   - Build command: `docker build --target base -t markerengine .`

2. **Import errors in container**
   - Solution: The PYTHONPATH is set correctly in the Dockerfile
   - Ensure you're copying the entire backend directory

3. **Health check failures**
   - Solution: Wait for the application to fully start (40s grace period)
   - Check container logs: `docker logs <container-id>`

4. **Large image size**
   - Solution: Use the `base` stage and ensure .dockerignore is present
   - Production image should be ~200-300MB

### Debug Commands

```bash
# Check image sizes
docker images markerengine-core

# Run container with shell access
docker run -it --entrypoint /bin/bash markerengine-core:latest

# View container logs
docker logs -f <container-id>

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/health/live
curl http://localhost:8000/api/health/ready
```

## 📊 Performance Optimization

### Image Size Optimization

- **Production image**: ~200-300MB (base stage)
- **Development image**: ~800MB+ (spark stage)
- Use `.dockerignore` to exclude unnecessary files
- Multi-stage build reduces final image size

### Resource Requirements

**Base Stage (Production)**:
- Memory: 256-512MB
- CPU: 0.25-0.5 vCPU
- Storage: 1GB

**Spark Stage**:
- Memory: 1-2GB minimum
- CPU: 1+ vCPU
- Storage: 2GB+

## 🔐 Security Best Practices

1. **Run as non-root user** (consider adding in future)
2. **Use official Python base images**
3. **Keep dependencies updated**
4. **Use secrets for sensitive configuration**
5. **Enable HTTPS in production**

## 📝 Example Commands

```bash
# Full build and test pipeline
./docker-build.sh markerengine-core v1.0.0

# Deploy to Fly.io with specific tag
flyctl deploy --image markerengine-core:v1.0.0

# Run with custom environment
docker run -e DATABASE_URL="mongodb://localhost:27017" -p 8000:8000 markerengine-core:latest

# Scale on Fly.io
flyctl scale count 2

# View logs on Fly.io
flyctl logs
```

## 🆘 Support

If you encounter issues:

1. Check the build logs for errors
2. Verify environment variables are set correctly
3. Ensure health checks are passing
4. Check platform-specific documentation:
   - [Fly.io Docs](https://fly.io/docs/)
   - [Railway Docs](https://docs.railway.app/)
   - [Render Docs](https://render.com/docs)

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ Docker build completes without errors
- ✅ Health check returns HTTP 200
- ✅ Application starts within 40 seconds
- ✅ No Java-related errors in logs
- ✅ API responds to basic requests