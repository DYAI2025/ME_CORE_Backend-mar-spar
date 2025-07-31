# ME_CORE_Backend-mar-spar Deployment Guide

## 🚀 Render Deployment

This guide covers deploying the MarkerEngine Core system to Render with full CI/CD, monitoring dashboard, and end-to-end testing.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Repository must be connected to Render
3. **Environment Variables**: Prepare the following secrets:
   - `RENDER_API_KEY` - Your Render API key
   - `RENDER_SERVICE_ID_BACKEND` - Backend service ID
   - `RENDER_SERVICE_ID_DASHBOARD` - Dashboard service ID
   - `RENDER_SERVICE_ID_SPARK` - Spark service ID (optional)
   - `JENKINS_API_TOKEN` - Jenkins API token for monitoring
   - `AWS_ACCESS_KEY_ID` - For backup storage (optional)
   - `AWS_SECRET_ACCESS_KEY` - For backup storage (optional)

## Deployment Architecture

```
┌─────────────────────┐
│   GitHub Actions    │
│     (CI/CD)         │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │   Render    │
    │  Platform   │
    └──────┬──────┘
           │
    ┌──────▼────────────────────────┐
    │         Services              │
    ├───────────────────────────────┤
    │ • Backend API (FastAPI)       │
    │ • Dashboard (Next.js)         │
    │ • Spark NLP (Optional)        │
    │ • MongoDB Database            │
    │ • Redis Cache                 │
    └───────────────────────────────┘
```

## Step 1: Initial Setup

### 1.1 Fork/Clone Repository
```bash
git clone https://github.com/DYAI2025/ME_CORE_Backend-mar-spar.git
cd ME_CORE_Backend-mar-spar
```

### 1.2 Configure Render Blueprint
The `render.yaml` file is already configured. Review and adjust:
- Service names
- Plan types (starter, standard, pro)
- Environment variables

## Step 2: Deploy to Render

### 2.1 Using Render Dashboard

1. **Connect GitHub**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the `ME_CORE_Backend-mar-spar` repository

2. **Configure Services**:
   - Render will detect `render.yaml` automatically
   - Review the services to be created:
     - `me-core-backend` - Backend API
     - `me-core-dashboard` - Monitoring Dashboard
     - `me-core-spark` - Spark NLP (optional)
     - `me-core-mongodb` - Database
     - `me-core-redis` - Cache

3. **Set Environment Variables**:
   ```
   JENKINS_URL=https://your-jenkins.com
   JENKINS_API_TOKEN=your-token
   S3_BUCKET=backup-bucket-name
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   ```

4. **Deploy**:
   - Click "Apply"
   - Wait for all services to be created and deployed

### 2.2 Using Render CLI

```bash
# Install Render CLI
brew install render/render/render

# Login
render login

# Deploy blueprint
render blueprint deploy
```

## Step 3: Configure CI/CD

### 3.1 GitHub Secrets

Add the following secrets to your GitHub repository:

```bash
# Go to Settings → Secrets → Actions
RENDER_API_KEY=your-render-api-key
RENDER_SERVICE_ID_BACKEND=srv-xxxxx
RENDER_SERVICE_ID_DASHBOARD=srv-xxxxx
RENDER_SERVICE_ID_SPARK=srv-xxxxx
```

### 3.2 Enable GitHub Actions

The workflow is already configured in `.github/workflows/deploy-render.yml`.
It will automatically:
- Run tests on push to main/staging
- Deploy to staging on push to staging branch
- Deploy to production on push to main branch
- Run E2E tests after deployment

## Step 4: Access Dashboard

### 4.1 Dashboard URL

After deployment, access your dashboard at:
```
https://me-core-dashboard.onrender.com
```

### 4.2 Dashboard Features

1. **System Health Monitoring**:
   - Real-time health status
   - Component status (API, DB, Redis, Spark)
   - Response times and latencies

2. **Marker Management**:
   - View all active markers
   - Edit DETECT registry with GUI
   - View and manage schemas

3. **Jenkins Integration**:
   - Build status
   - Queue information
   - Recent builds

4. **Quick Actions**:
   - Deploy to staging/production
   - Trigger E2E tests
   - System refresh

## Step 5: Monitoring & Maintenance

### 5.1 Health Checks

Backend health endpoint:
```bash
curl https://me-core-backend.onrender.com/api/health/live
```

Dashboard health endpoint:
```bash
curl https://me-core-dashboard.onrender.com/api/health
```

### 5.2 Logs

View logs in Render Dashboard or using CLI:
```bash
render logs me-core-backend --tail
render logs me-core-dashboard --tail
```

### 5.3 Metrics

Access Prometheus metrics:
```bash
curl https://me-core-backend.onrender.com/metrics
```

## Step 6: E2E Testing

### 6.1 Manual Testing

Run E2E tests locally:
```bash
cd tests/e2e
npm install
npm test
```

### 6.2 Automated Testing

E2E tests run automatically after deployment.
View results in GitHub Actions.

### 6.3 Test Coverage

- Dashboard loading and navigation
- Marker management functionality
- DETECT registry editing
- Jenkins integration
- API integration
- Performance benchmarks

## Step 7: Backup & Recovery

### 7.1 Automatic Backups

Daily backups are configured via cron job:
- MongoDB data backed up to S3
- Configurations saved
- Marker definitions preserved

### 7.2 Manual Backup

```bash
# Trigger manual backup
curl -X POST https://me-core-backend.onrender.com/api/dashboard/backup \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7.3 Restore

```bash
# Restore from backup
curl -X POST https://me-core-backend.onrender.com/api/dashboard/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"backup_id": "backup-20240115-120000"}'
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   - Check environment variables
   - Review service logs
   - Verify database connection

2. **Dashboard Can't Connect to Backend**:
   - Check CORS settings
   - Verify API URL configuration
   - Review network settings

3. **E2E Tests Failing**:
   - Check service URLs
   - Verify test environment
   - Review test logs

### Debug Mode

Enable debug logging:
```bash
# Backend
PYTHON_ENV=development
LOG_LEVEL=DEBUG

# Dashboard
NODE_ENV=development
```

## Security Considerations

1. **Authentication**:
   - Dashboard requires authentication (configured separately)
   - API uses JWT tokens
   - Jenkins integration uses API tokens

2. **Network Security**:
   - All services use HTTPS
   - Private services not exposed to internet
   - Database connections encrypted

3. **Access Control**:
   - Role-based access for dashboard
   - API key authentication
   - IP allowlisting available

## Performance Optimization

1. **Caching**:
   - Redis cache for frequently accessed data
   - Browser caching for static assets
   - API response caching

2. **Scaling**:
   - Horizontal scaling supported
   - Auto-scaling based on CPU/memory
   - Load balancing built-in

3. **Monitoring**:
   - Real-time performance metrics
   - Alert thresholds configured
   - Performance dashboards

## Support

- **Documentation**: See `/docs` directory
- **Issues**: GitHub Issues
- **Monitoring**: Dashboard at `https://me-core-dashboard.onrender.com`

## Next Steps

1. Configure authentication for dashboard
2. Set up monitoring alerts
3. Configure custom domains
4. Enable auto-scaling
5. Set up staging environment