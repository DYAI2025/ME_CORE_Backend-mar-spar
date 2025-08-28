# 🔗 MarkerEngine Backend-Frontend API Integration

This document describes the complete integration between the MarkerEngine backend and frontend applications.

## 🎯 Integration Overview

The MarkerEngine system now has **complete API integration** between:
- **Backend**: FastAPI REST API with WebSocket support
- **Frontend**: Next.js user interface for text analysis
- **Dashboard**: Next.js admin interface for system management

## ✅ Implementation Status

### ✅ Complete Features

#### 🔄 API Client Implementation
- **Centralized API clients** in both frontend and dashboard
- **Type-safe requests** with TypeScript interfaces
- **Comprehensive error handling** with custom error types
- **Automatic request/response transformation**

#### 🌐 Endpoint Integration
All backend endpoints are integrated:

| Category | Endpoints | Status |
|----------|-----------|--------|
| **Analysis** | `/analyze` (POST) | ✅ Integrated |
| **Schemas** | `/api/schemas/` (CRUD) | ✅ Integrated |
| **Markers** | `/markers/` (GET, POST) | ✅ Integrated |
| **Health** | `/healthz`, `/metrics/health`, `/metrics/ready`, `/metrics/live` | ✅ Integrated |
| **Dashboard** | `/api/dashboard/overview` | ✅ Integrated |
| **Metrics** | `/metrics` (Prometheus) | ✅ Integrated |

#### 🔌 WebSocket Integration
- **Real-time updates** via `/api/dashboard/ws`
- **Auto-reconnection** with exponential backoff
- **Heartbeat mechanism** for connection health
- **Custom React hook** for easy WebSocket management

#### ⚙️ Configuration
- **Proxy routing** configured in Next.js
- **Environment-based** API URL configuration
- **CORS headers** properly configured
- **Development and production** ready

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │◀────│    Dashboard    │
│   (Next.js)     │     │   (FastAPI)     │     │   (Next.js)     │
│                 │     │                 │     │                 │
│ • API Client    │     │ • REST Routes   │     │ • Admin API     │
│ • WebSocket     │     │ • WebSocket     │     │ • Monitoring    │
│ • Type Safety   │     │ • Prometheus    │     │ • Management    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 📁 File Structure

```
ME_CORE_Backend-mar-spar/
├── frontend/
│   ├── src/lib/api.ts              # 🔧 Main API client
│   ├── src/hooks/useWebSocket.ts   # 🔌 WebSocket hook
│   ├── src/types/index.ts          # 📝 TypeScript types
│   ├── next.config.js              # ⚙️ Proxy configuration
│   ├── .env.example                # 🔧 Environment template
│   └── API_MAP.md                  # 📚 Complete documentation
├── dashboard/
│   ├── src/lib/api.ts              # 🔧 Dashboard API client
│   ├── next.config.js              # ⚙️ Proxy + Jenkins config
│   └── .env.example                # 🔧 Environment template
├── backend/
│   ├── api/                        # 🎯 All API endpoints
│   └── main.py                     # 🚀 FastAPI application
└── test-api-integration.js         # 🧪 Integration test script
```

## 🚀 Quick Start

### 1. Setup Environment

**Frontend:**
```bash
cd frontend
cp .env.example .env.local
# Edit .env.local with your backend URL
```

**Dashboard:**
```bash
cd dashboard  
cp .env.example .env.local
# Edit .env.local with your backend and Jenkins URLs
```

### 2. Install Dependencies

```bash
# Frontend
cd frontend && npm install

# Dashboard  
cd dashboard && npm install
```

### 3. Start Development

```bash
# Start backend (in one terminal)
cd backend && uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend && npm run dev

# Start dashboard (in third terminal)
cd dashboard && npm run dev
```

### 4. Test Integration

```bash
# Run API integration test
node test-api-integration.js
```

## 💻 Usage Examples

### Frontend API Usage

```typescript
import { api, analysisApi, schemaApi } from '@/lib/api'

// Text Analysis
const result = await api.analyze({
  text: "Sample text to analyze",
  schemaId: "SCH_relation_analyse_schema",
  options: { highlightMarkers: true }
})

// Schema Management
const schemas = await schemaApi.getSchemas()
const newSchema = await schemaApi.createSchema({
  name: "Custom Schema",
  version: "1.0.0",
  description: "My custom analysis schema",
  fields: [],
  metadata: {}
})
```

### WebSocket Integration

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

function LiveLogComponent() {
  const { connection, messages, connect, disconnect } = useWebSocket('/api/dashboard/ws', {
    autoConnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5
  })

  return (
    <div>
      <div>Status: {connection.isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      <div>
        {messages.map((msg, idx) => (
          <div key={idx}>{msg.payload.message}</div>
        ))}
      </div>
    </div>
  )
}
```

### Dashboard API Usage

```typescript
import { 
  fetchDashboardData, 
  triggerDeployment, 
  fetchSystemHealth 
} from '@/lib/api'

// Get comprehensive dashboard data
const data = await fetchDashboardData()

// Trigger deployment
await triggerDeployment('production')

// Check system health
const health = await fetchSystemHealth()
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `NEXT_PUBLIC_JENKINS_URL` | Jenkins URL (dashboard only) | `http://localhost:8080` |

### Proxy Configuration

Both frontends use Next.js rewrites for API proxying:

```javascript
// frontend/next.config.js & dashboard/next.config.js
async rewrites() {
  return [
    {
      source: '/api/backend/:path*',
      destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
    }
  ]
}
```

## 🛡️ Error Handling

The integration includes comprehensive error handling:

```typescript
try {
  const result = await api.analyze(request)
  // Handle success
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.code, error.message)
    // Handle specific API errors
  } else {
    console.error('Network Error:', error.message)
    // Handle network/connection errors
  }
}
```

## 📊 Type Safety

All API interactions are fully typed:

```typescript
interface AnalysisRequest {
  text: string
  schemaId: string
  options?: {
    highlightMarkers?: boolean
    includeConfidence?: boolean
    maxResults?: number
  }
}

interface AnalysisResponse {
  markers: any[]
  detection: DetectionEntry[]
  interpretation: string
  model_used?: string
  processing_time?: number
  marker_count: number
  total_score: number
}
```

## 🧪 Testing

### Manual Testing
```bash
# Test API endpoints
node test-api-integration.js

# Test TypeScript compilation
cd frontend && npm run type-check
cd dashboard && npx tsc --noEmit
```

### Integration Testing
The implementation includes comprehensive error scenarios:
- Network failures
- Backend unavailability  
- Invalid responses
- WebSocket disconnections

## 🚀 Deployment

### Production Configuration

```bash
# Production environment variables
NEXT_PUBLIC_API_URL=https://api.markerengine.example.com
NEXT_PUBLIC_WS_URL=wss://api.markerengine.example.com
NEXT_PUBLIC_JENKINS_URL=https://jenkins.markerengine.example.com
```

### Build Commands

```bash
# Frontend
cd frontend && npm run build && npm start

# Dashboard
cd dashboard && npm run build && npm start
```

## 📚 Documentation

- **[Complete API Map](frontend/API_MAP.md)**: Detailed endpoint documentation
- **Backend API Docs**: Available at `/docs` when backend is running
- **Component Documentation**: TypeScript interfaces in `/src/types/`

## 🎯 Next Steps

The API integration is **complete and ready for use**. Future enhancements could include:

1. **Authentication Integration**: JWT-based auth
2. **Caching Layer**: Redis integration for performance
3. **File Upload**: Document analysis endpoints
4. **Batch Processing**: Bulk analysis capabilities
5. **Real-time Analytics**: Enhanced WebSocket features

## ✨ Summary

**✅ Complete Backend-Frontend Integration Achieved:**
- 🔧 **8 endpoint categories** fully integrated
- 🔌 **WebSocket real-time** communication
- 🛡️ **Type-safe API calls** with error handling
- ⚙️ **Environment-based** configuration
- 📚 **Comprehensive documentation**
- 🧪 **Integration testing** tools

The MarkerEngine system now provides a **seamless, production-ready connection** between all frontend applications and the FastAPI backend! 🚀