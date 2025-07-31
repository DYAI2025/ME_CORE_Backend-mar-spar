# Deploy MarkerEngine Backend to Render

This guide walks you through deploying the MarkerEngine Backend API to Render.com.

## Quick Start

The application is configured to run in **mock mode** by default, which means it doesn't require MongoDB and will work immediately upon deployment.

## Deployment Steps

### 1. Prerequisites
- A [Render.com](https://render.com) account
- This repository pushed to GitHub, GitLab, or Bitbucket

### 2. Deploy to Render

#### Option A: Using the Render Dashboard

1. Log in to your [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your Git repository
4. Configure the service:
   - **Name**: `markerengine-backend` (or your preferred name)
   - **Region**: Choose your preferred region
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: `backend` (important!)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**

#### Option B: Using render.yaml (Recommended)

1. The `render.yaml` file is already configured in this directory
2. Push your code to your Git repository
3. In Render Dashboard:
   - Click **New +** → **Blueprint**
   - Connect your repository
   - Render will automatically detect the `render.yaml` file
   - Click **Apply** to create the service

### 3. Environment Variables (Optional)

The service runs in mock mode by default. If you want to enable additional features:

#### LLM Integration (Optional)
Add these in the Render Dashboard under **Environment**:
- `MOONSHOT_API_KEY`: Your Moonshot/Kimi API key
- `OPENAI_API_KEY`: Your OpenAI API key (fallback)

#### MongoDB Integration (Optional)
To use real MongoDB instead of mock mode:
1. Create a MongoDB instance (e.g., MongoDB Atlas)
2. Update `DATABASE_URL` with your connection string

### 4. Verify Deployment

Once deployed, your service will be available at:
```
https://[your-service-name].onrender.com
```

Test endpoints:
- Health check: `https://[your-service-name].onrender.com/api/health/live`
- API docs: `https://[your-service-name].onrender.com/docs`
- Root: `https://[your-service-name].onrender.com/`

## Features in Mock Mode

The mock service provides:
- ✅ Full API functionality
- ✅ Sample markers for testing
- ✅ Text analysis with pattern matching
- ✅ No database required
- ✅ Immediate deployment

## Monitoring

- Check deployment logs in Render Dashboard
- Monitor service health at `/api/health/live`
- View API documentation at `/docs`
- Prometheus metrics available at `/metrics` (if enabled)

## Troubleshooting

### Service Won't Start
- Check the **Logs** tab in Render Dashboard
- Ensure `backend` is set as the root directory
- Verify Python version compatibility

### 500 Errors
- Check environment variables are set correctly
- Review application logs for configuration errors

### Performance Issues
- The free tier may have cold starts
- Consider upgrading for better performance

## Next Steps

1. Test the API using the interactive docs at `/docs`
2. Configure environment variables for additional features
3. Set up monitoring and alerts in Render Dashboard
4. Consider adding a custom domain

## Support

- [Render Documentation](https://docs.render.com)
- [MarkerEngine Issues](https://github.com/your-repo/issues)
- Check application logs in Render Dashboard for debugging