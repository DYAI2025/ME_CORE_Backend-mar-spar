# 🚀 Fly.io Deployment Checklist

## Pre-Deployment Setup

### 1. MongoDB Atlas Setup (Required)
- [ ] Create MongoDB Atlas account (free tier)
- [ ] Create cluster and database user
- [ ] Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/marker_engine`
- [ ] Whitelist IP: `0.0.0.0/0` (for fly.io access)

### 2. Fly.io Setup
- [ ] Install flyctl: `curl -L https://fly.io/install.sh | sh`
- [ ] Login: `flyctl auth login`
- [ ] Set database secret: `flyctl secrets set DATABASE_URL="your_mongodb_connection"`

### 3. Optional Configuration
- [ ] Set API keys: `flyctl secrets set MOONSHOT_API_KEY="your_key"`
- [ ] Review app name in fly.toml (default: me-core-backend)

## Deployment

### Quick Deploy
```bash
./deploy-to-fly.sh
```

### Manual Deploy
```bash
flyctl deploy
```

### Verification
- [ ] Check status: `flyctl status`
- [ ] Test health: `curl https://your-app.fly.dev/health`
- [ ] View logs: `flyctl logs`

## Post-Deployment

### Monitoring
- [ ] Set up log monitoring
- [ ] Test API endpoints
- [ ] Monitor resource usage

### Scaling (if needed)
```bash
flyctl scale vm shared-cpu-1x --memory 512
flyctl scale count 2
```

## Troubleshooting

### Common Issues
1. **MongoDB Connection Error**: Check connection string and IP whitelist
2. **Memory Issues**: Scale up VM size
3. **Build Failures**: Check logs with `flyctl logs`

### Resources
- [Fly.io Documentation](https://fly.io/docs/)
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/getting-started/)
