# 🚄 Railway Deployment Checklist for ME_CORE Backend

## 📋 Pre-Deployment Checklist

### 1. **Railway Account Setup**
- [ ] Create Railway account at [railway.app](https://railway.app)
- [ ] Verify email address
- [ ] Add payment method (optional, but recommended for production)

### 2. **Local Prerequisites**
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Clone repository: `git clone https://github.com/DYAI2025/ME_CORE_Backend-mar-spar.git`
- [ ] Navigate to project: `cd ME_CORE_Backend-mar-spar`

### 3. **Code Preparation**
- [ ] ✅ Backend port configuration updated (handles $PORT)
- [ ] ✅ Dockerfile updated for Railway compatibility
- [ ] ✅ Environment template created (.env.railway.example)
- [ ] ✅ Deployment script ready (deploy-to-railway.sh)

## 🚀 Deployment Steps

### Option A: Automated Deployment (Recommended)
```bash
# Run the deployment script
./deploy-to-railway.sh
```

### Option B: Manual Deployment

#### 1. **Login to Railway**
```bash
railway login
```

#### 2. **Create New Project**
```bash
railway init --name me-core-backend
```

#### 3. **Add MongoDB Service**
```bash
railway add --plugin mongodb
```

#### 4. **Add Redis Service (Optional)**
```bash
railway add --plugin redis
```

#### 5. **Set Environment Variables**
```bash
# Core variables
railway variables set ENVIRONMENT=production
railway variables set PYTHON_ENV=production
railway variables set MONGO_DB_NAME=marker_engine
railway variables set ENABLE_METRICS=true
railway variables set SPARK_NLP_ENABLED=false

# Cache configuration
railway variables set CACHE_TYPE=redis
railway variables set CACHE_DEFAULT_TTL=3600

# Optional API keys
railway variables set MOONSHOT_API_KEY=your_key_here
railway variables set OPENAI_API_KEY=your_key_here
```

#### 6. **Deploy**
```bash
railway up
```

## ✅ Post-Deployment Verification

### 1. **Check Deployment Status**
- [ ] Visit Railway dashboard
- [ ] Check build logs for errors
- [ ] Verify service is "Active"

### 2. **Test Endpoints**
```bash
# Health check
curl https://[your-app].up.railway.app/api/health/live

# API root
curl https://[your-app].up.railway.app/

# Swagger docs
# Visit: https://[your-app].up.railway.app/docs
```

### 3. **Verify Database Connection**
- [ ] Check Railway logs for MongoDB connection success
- [ ] Test a simple API operation that uses the database

### 4. **Monitor Performance**
- [ ] Check memory usage in Railway dashboard
- [ ] Monitor response times
- [ ] Review error logs

## 🔧 Troubleshooting

### Common Issues:

1. **Port Binding Error**
   - Solution: Ensure the app uses `$PORT` environment variable
   - Already fixed in our configuration ✅

2. **MongoDB Connection Failed**
   - Check: `DATABASE_URL` is properly set
   - Format: `mongodb://...` (Railway provides this automatically)

3. **Module Import Errors**
   - Check: All dependencies in requirements.txt
   - Solution: Rebuild with `railway up --force`

4. **Memory Limit Exceeded**
   - Solution: Disable Spark NLP if not needed
   - Set: `SPARK_NLP_ENABLED=false`

## 📊 Configuration Summary

### Required Environment Variables:
```env
DATABASE_URL=${{MongoDB.DATABASE_URL}}  # Auto-provided by Railway
ENVIRONMENT=production
MONGO_DB_NAME=marker_engine
```

### Optional Environment Variables:
```env
REDIS_URL=${{Redis.REDIS_URL}}  # If Redis added
MOONSHOT_API_KEY=your_key
OPENAI_API_KEY=your_key
ENABLE_METRICS=true
SPARK_NLP_ENABLED=false
```

## 🎯 Success Criteria

- [ ] Backend service is running (green status)
- [ ] Health endpoint returns 200 OK
- [ ] MongoDB connection established
- [ ] API documentation accessible at /docs
- [ ] No error logs in first 5 minutes

## 📝 Notes

- Railway automatically handles SSL/TLS certificates
- Custom domains can be added later in Railway dashboard
- MongoDB backups are automatic (daily)
- Scaling can be configured in Railway settings

## 🆘 Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Project Issues: [GitHub Issues](https://github.com/DYAI2025/ME_CORE_Backend-mar-spar/issues)