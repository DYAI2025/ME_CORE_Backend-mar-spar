# Schema API Endpoints

This document describes the new dedicated schema management API endpoints.

## Base URL
All schema endpoints are available under `/api/schemas/`

## Endpoints

### 1. List All Schemas
**GET** `/api/schemas/`

Query Parameters:
- `active_only` (boolean, default: true) - Filter to show only active schemas

Response: Array of schema objects

Example:
```bash
curl -X GET "http://localhost:8000/api/schemas/"
```

### 2. Get Specific Schema
**GET** `/api/schemas/{schema_id}`

Path Parameters:
- `schema_id` (string) - MongoDB ObjectId of the schema

Response: Single schema object

Example:
```bash
curl -X GET "http://localhost:8000/api/schemas/507f1f77bcf86cd799439011"
```

### 3. Create New Schema
**POST** `/api/schemas/`

Request Body:
```json
{
  "name": "my-schema",
  "version": "1.0.0",
  "description": "A sample schema",
  "fields": [
    {
      "name": "field1",
      "type": "string",
      "required": true
    }
  ],
  "metadata": {}
}
```

Response: Created schema object

Example:
```bash
curl -X POST "http://localhost:8000/api/schemas/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-schema", "version": "1.0.0"}'
```

### 4. Update Schema
**PUT** `/api/schemas/{schema_id}`

Path Parameters:
- `schema_id` (string) - MongoDB ObjectId of the schema

Request Body (all fields optional):
```json
{
  "name": "updated-schema",
  "version": "1.1.0",
  "description": "Updated description",
  "fields": [...],
  "metadata": {},
  "active": true
}
```

Response: Updated schema object

Example:
```bash
curl -X PUT "http://localhost:8000/api/schemas/507f1f77bcf86cd799439011" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.1.0"}'
```

### 5. Delete Schema
**DELETE** `/api/schemas/{schema_id}`

Path Parameters:
- `schema_id` (string) - MongoDB ObjectId of the schema

Query Parameters:
- `hard_delete` (boolean, default: false) - Permanently delete vs. soft delete

Response: Success message

Example:
```bash
# Soft delete (marks as inactive)
curl -X DELETE "http://localhost:8000/api/schemas/507f1f77bcf86cd799439011"

# Hard delete (permanently removes)
curl -X DELETE "http://localhost:8000/api/schemas/507f1f77bcf86cd799439011?hard_delete=true"
```

### 6. Reactivate Schema
**POST** `/api/schemas/{schema_id}/activate`

Path Parameters:
- `schema_id` (string) - MongoDB ObjectId of the schema

Response: Success message

Example:
```bash
curl -X POST "http://localhost:8000/api/schemas/507f1f77bcf86cd799439011/activate"
```

## Schema Object Structure

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "schema-name",
  "version": "1.0.0",
  "description": "Schema description",
  "fields": [
    {
      "name": "field_name",
      "type": "string",
      "required": true,
      "validation": {}
    }
  ],
  "active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "metadata": {}
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad Request (invalid input)
- `404` - Not Found (schema doesn't exist)
- `409` - Conflict (duplicate name)
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Dashboard Integration

The dashboard continues to have its own schema summary endpoint at `/api/dashboard/schemas/summary` which provides a simplified view optimized for dashboard display.

The new `/api/schemas/` endpoints are designed for full CRUD operations and detailed schema management.