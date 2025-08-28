# MarkerEngine API Integration Map

This document provides a comprehensive overview of how all backend endpoints are integrated into the frontend applications.

## 🏗️ Architecture Overview

The MarkerEngine system consists of:
- **Backend**: FastAPI-based REST API (`http://localhost:8000`)
- **Frontend**: Next.js user interface (`/frontend/`)
- **Dashboard**: Next.js admin interface (`/dashboard/`)

## 📡 Backend Endpoint Mapping

### Core Analysis Endpoints

| Backend Endpoint | Method | Frontend Integration | Purpose |
|------------------|--------|---------------------|---------|
| `/analyze` | POST | `analysisApi.analyze()` | Text analysis with marker detection |
| `/analyze/v2` | POST | Not integrated | Advanced analysis (future) |

**Frontend Usage:**
```typescript
import { analysisApi } from '@/lib/api'

const result = await analysisApi.analyze({
  text: "Sample text to analyze",
  schemaId: "SCH_relation_analyse_schema",
  options: { highlightMarkers: true }
})
```

### Schema Management Endpoints

| Backend Endpoint | Method | Frontend Integration | Purpose |
|------------------|--------|---------------------|---------|
| `/api/schemas` | GET | `schemaApi.getSchemas()` | List all schemas |
| `/api/schemas/{id}` | GET | `schemaApi.getSchema(id)` | Get specific schema |
| `/api/schemas` | POST | `schemaApi.createSchema()` | Create new schema |
| `/api/schemas/{id}` | PUT | `schemaApi.updateSchema()` | Update schema |
| `/api/schemas/{id}` | DELETE | `schemaApi.deleteSchema()` | Delete/deactivate schema |
| `/api/schemas/{id}/activate` | POST | `schemaApi.activateSchema()` | Reactivate schema |

**Frontend Usage:**
```typescript
import { schemaApi } from '@/lib/api'

// Get all active schemas
const schemas = await schemaApi.getSchemas(true)

// Create new schema
const newSchema = await schemaApi.createSchema({
  name: "New Analysis Schema",
  version: "1.0.0",
  description: "Custom schema for specific analysis",
  fields: [],
  metadata: {}
})
```

### Marker Management Endpoints

| Backend Endpoint | Method | Frontend Integration | Purpose |
|------------------|--------|---------------------|---------|
| `/markers` | GET | `markerApi.getMarkers()` | List all markers |
| `/markers/{id}` | GET | `markerApi.getMarker(id)` | Get specific marker |
| `/markers` | POST | `markerApi.createMarker()` | Create new marker |

**Frontend Usage:**
```typescript
import { markerApi } from '@/lib/api'

// Get paginated markers
const markers = await markerApi.getMarkers(0, 50)

// Create new marker
const newMarker = await markerApi.createMarker({
  name: "Custom Marker",
  pattern: "specific pattern",
  weight: 1.0,
  category: "custom"
})
```

### Health & Monitoring Endpoints

| Backend Endpoint | Method | Frontend Integration | Purpose |
|------------------|--------|---------------------|---------|
| `/healthz` | GET | `healthApi.healthCheck()` | Basic health check |
| `/metrics/health` | GET | `healthApi.detailedHealth()` | Detailed health with system metrics |
| `/metrics/ready` | GET | `healthApi.readiness()` | Kubernetes readiness probe |
| `/metrics/live` | GET | `healthApi.liveness()` | Kubernetes liveness probe |
| `/metrics` | GET | `metricsApi.getMetrics()` | Prometheus metrics (text format) |

**Frontend Usage:**
```typescript
import { healthApi, metricsApi } from '@/lib/api'

// Basic health check
const health = await healthApi.healthCheck()

// Detailed system health
const systemHealth = await healthApi.detailedHealth()

// Get Prometheus metrics
const metrics = await metricsApi.getMetrics()
```

### Dashboard & Administration Endpoints

| Backend Endpoint | Method | Frontend Integration | Purpose |
|------------------|--------|---------------------|---------|
| `/api/dashboard/overview` | GET | `dashboardApi.getOverview()` | Dashboard overview data |
| `/api/dashboard/deploy/{env}` | POST | `triggerDeployment()` | Trigger deployment |
| `/api/dashboard/tests/e2e/trigger` | POST | `triggerE2ETests()` | Trigger E2E tests |
| `/api/dashboard/tests/results` | GET | `fetchTestResults()` | Get test results |

**Dashboard Usage:**
```typescript
import { fetchDashboardData, triggerDeployment } from '@/lib/api'

// Get comprehensive dashboard data
const dashboardData = await fetchDashboardData()

// Trigger production deployment
await triggerDeployment('production')
```

## 🔌 WebSocket Integration

### Real-time Updates

| Backend WebSocket | Frontend Integration | Purpose |
|-------------------|---------------------|---------|
| `/api/dashboard/ws` | `useWebSocket()` hook | Live logs and real-time updates |

**Frontend Usage:**
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const LiveLogComponent = () => {
  const { connection, messages, connect, disconnect } = useWebSocket('/api/dashboard/ws', {
    autoConnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5
  })

  return (
    <div>
      <div>Status: {connection.isConnected ? 'Connected' : 'Disconnected'}</div>
      <div>
        {messages.map((msg, idx) => (
          <div key={idx}>{msg.payload.message}</div>
        ))}
      </div>
    </div>
  )
}
```

## 🛣️ Routing & Proxy Configuration

### Frontend Proxy Setup (`frontend/next.config.js`)

```javascript
async rewrites() {
  return [
    {
      source: '/api/backend/:path*',
      destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/:path*`,
    },
  ]
}
```

### Dashboard Proxy Setup (`dashboard/next.config.js`)

```javascript
async rewrites() {
  return [
    {
      source: '/api/backend/:path*',
      destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
    },
    {
      source: '/api/jenkins/:path*',
      destination: `${process.env.NEXT_PUBLIC_JENKINS_URL || 'http://localhost:8080'}/:path*`,
    },
  ]
}
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# .env.local for Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Markerengine Frontend

# .env.local for Dashboard
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_JENKINS_URL=http://localhost:8080
```

### Production Configuration

```bash
# Production values
NEXT_PUBLIC_API_URL=https://api.markerengine.example.com
NEXT_PUBLIC_WS_URL=wss://api.markerengine.example.com
NEXT_PUBLIC_JENKINS_URL=https://jenkins.markerengine.example.com
```

## 📦 API Client Architecture

### Frontend API Client (`frontend/src/lib/api.ts`)

- **analysisApi**: Text analysis functionality
- **schemaApi**: Schema CRUD operations
- **markerApi**: Marker management
- **healthApi**: Health checks and monitoring
- **dashboardApi**: Dashboard data
- **metricsApi**: Prometheus metrics

### Dashboard API Client (`dashboard/src/lib/api.ts`)

- **fetchDashboardData()**: Comprehensive dashboard data
- **fetchMarkers()**: Marker management for admin
- **fetchSchemas()**: Schema management for admin
- **triggerDeployment()**: Deployment management
- **fetchJenkinsStatus()**: Jenkins integration
- **fetchSystemHealth()**: System monitoring

## 🔄 Error Handling

### API Error Structure

```typescript
interface ApiError {
  code: string
  message: string
  details?: any
  statusCode: number
}
```

### Error Handling Pattern

```typescript
try {
  const result = await analysisApi.analyze(request)
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

## 🧪 Testing Integration

### Frontend Testing

```typescript
// Test API integration
import { analysisApi } from '@/lib/api'

test('should analyze text successfully', async () => {
  const mockRequest = {
    text: "Test text",
    schemaId: "test-schema",
    options: { highlightMarkers: true }
  }
  
  const result = await analysisApi.analyze(mockRequest)
  expect(result.marker_count).toBeGreaterThanOrEqual(0)
})
```

### E2E Testing

```typescript
// E2E test with real backend
test('full analysis workflow', async () => {
  // 1. Get available schemas
  const schemas = await schemaApi.getSchemas()
  expect(schemas.length).toBeGreaterThan(0)
  
  // 2. Run analysis
  const result = await analysisApi.analyze({
    text: "Sample analysis text",
    schemaId: schemas[0].id
  })
  
  // 3. Verify results
  expect(result.interpretation).toBeDefined()
})
```

## 🚀 Deployment Considerations

### Build-time Integration

- API endpoints are configured via environment variables
- Proxy rules are set up in Next.js configuration
- WebSocket connections handle reconnection automatically

### Runtime Integration

- Health checks ensure backend availability
- Error boundaries handle API failures gracefully
- Retry logic for failed requests
- Connection management for WebSocket

## 📝 Future Enhancements

### Planned Integrations

1. **Authentication Endpoints**: JWT-based auth integration
2. **File Upload**: Document analysis endpoints
3. **Batch Processing**: Bulk analysis endpoints
4. **Real-time Analytics**: Enhanced WebSocket features
5. **Caching Layer**: Redis integration for performance

### API Versioning

- Support for multiple API versions (`/analyze/v2`)
- Backward compatibility for existing integrations
- Gradual migration path for breaking changes

---

## 📞 Connection Summary

**Frontend → Backend Connection:**
- Direct HTTP API calls via fetch
- WebSocket for real-time updates
- Proxy routing for development
- Environment-based configuration

**Dashboard → Backend Connection:**
- Administrative API operations
- System monitoring integration
- Deployment management
- Jenkins integration for CI/CD

**Error Handling:**
- Comprehensive error types
- Retry mechanisms
- User-friendly error messages
- Logging for debugging

This integration provides a complete, type-safe, and maintainable connection between the MarkerEngine frontend applications and the FastAPI backend.