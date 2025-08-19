"""
Schema API endpoints for managing schemas
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field

from ..database import get_database
from ..src.shared.types import SchemaRequest, SchemaInfo

router = APIRouter(prefix="/api/schemas", tags=["schemas"])


class SchemaCreateRequest(BaseModel):
    """Schema creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="1.0.0")
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SchemaUpdateRequest(BaseModel):
    """Schema update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class SchemaResponse(BaseModel):
    """Schema response model"""
    id: str
    name: str
    version: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]
    active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


@router.get("/", response_model=List[SchemaResponse])
async def get_schemas(
    active_only: bool = True,
    db = Depends(get_database)
):
    """Get all schemas"""
    try:
        schemas_collection = db.schemas
        filter_query = {"active": True} if active_only else {}
        
        schemas = []
        async for schema in schemas_collection.find(filter_query).sort("created_at", -1):
            schemas.append(SchemaResponse(
                id=str(schema["_id"]),
                name=schema["name"],
                version=schema.get("version", "1.0.0"),
                description=schema.get("description"),
                fields=schema.get("fields", []),
                active=schema.get("active", True),
                created_at=schema.get("created_at", datetime.utcnow()),
                updated_at=schema.get("updated_at", datetime.utcnow()),
                metadata=schema.get("metadata", {})
            ))
        
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schemas: {str(e)}")


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(
    schema_id: str,
    db = Depends(get_database)
):
    """Get a specific schema by ID"""
    try:
        schemas_collection = db.schemas
        
        # Validate ObjectId format
        if not ObjectId.is_valid(schema_id):
            raise HTTPException(status_code=400, detail="Invalid schema ID format")
        
        schema = await schemas_collection.find_one({"_id": ObjectId(schema_id)})
        
        if not schema:
            raise HTTPException(status_code=404, detail="Schema not found")
        
        return SchemaResponse(
            id=str(schema["_id"]),
            name=schema["name"],
            version=schema.get("version", "1.0.0"),
            description=schema.get("description"),
            fields=schema.get("fields", []),
            active=schema.get("active", True),
            created_at=schema.get("created_at", datetime.utcnow()),
            updated_at=schema.get("updated_at", datetime.utcnow()),
            metadata=schema.get("metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")


@router.post("/", response_model=SchemaResponse)
async def create_schema(
    request: SchemaCreateRequest,
    db = Depends(get_database)
):
    """Create a new schema"""
    try:
        schemas_collection = db.schemas
        
        # Check if schema with same name already exists
        existing_schema = await schemas_collection.find_one({"name": request.name, "active": True})
        if existing_schema:
            raise HTTPException(status_code=409, detail="Schema with this name already exists")
        
        # Create new schema document
        now = datetime.utcnow()
        schema_doc = {
            "name": request.name,
            "version": request.version,
            "description": request.description,
            "fields": request.fields,
            "active": True,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata
        }
        
        # Insert into database
        result = await schemas_collection.insert_one(schema_doc)
        schema_doc["_id"] = result.inserted_id
        
        return SchemaResponse(
            id=str(schema_doc["_id"]),
            name=schema_doc["name"],
            version=schema_doc["version"],
            description=schema_doc["description"],
            fields=schema_doc["fields"],
            active=schema_doc["active"],
            created_at=schema_doc["created_at"],
            updated_at=schema_doc["updated_at"],
            metadata=schema_doc["metadata"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schema: {str(e)}")


@router.put("/{schema_id}", response_model=SchemaResponse)
async def update_schema(
    schema_id: str,
    request: SchemaUpdateRequest,
    db = Depends(get_database)
):
    """Update an existing schema"""
    try:
        schemas_collection = db.schemas
        
        # Validate ObjectId format
        if not ObjectId.is_valid(schema_id):
            raise HTTPException(status_code=400, detail="Invalid schema ID format")
        
        # Check if schema exists
        existing_schema = await schemas_collection.find_one({"_id": ObjectId(schema_id)})
        if not existing_schema:
            raise HTTPException(status_code=404, detail="Schema not found")
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if request.name is not None:
            # Check if new name conflicts with another schema
            name_conflict = await schemas_collection.find_one({
                "name": request.name,
                "active": True,
                "_id": {"$ne": ObjectId(schema_id)}
            })
            if name_conflict:
                raise HTTPException(status_code=409, detail="Schema with this name already exists")
            update_doc["name"] = request.name
        
        if request.version is not None:
            update_doc["version"] = request.version
        if request.description is not None:
            update_doc["description"] = request.description
        if request.fields is not None:
            update_doc["fields"] = request.fields
        if request.metadata is not None:
            update_doc["metadata"] = request.metadata
        if request.active is not None:
            update_doc["active"] = request.active
        
        # Update in database
        await schemas_collection.update_one(
            {"_id": ObjectId(schema_id)},
            {"$set": update_doc}
        )
        
        # Retrieve updated schema
        updated_schema = await schemas_collection.find_one({"_id": ObjectId(schema_id)})
        
        return SchemaResponse(
            id=str(updated_schema["_id"]),
            name=updated_schema["name"],
            version=updated_schema["version"],
            description=updated_schema.get("description"),
            fields=updated_schema.get("fields", []),
            active=updated_schema.get("active", True),
            created_at=updated_schema.get("created_at", datetime.utcnow()),
            updated_at=updated_schema["updated_at"],
            metadata=updated_schema.get("metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schema: {str(e)}")


@router.delete("/{schema_id}")
async def delete_schema(
    schema_id: str,
    hard_delete: bool = False,
    db = Depends(get_database)
):
    """Delete a schema (soft delete by default)"""
    try:
        schemas_collection = db.schemas
        
        # Validate ObjectId format
        if not ObjectId.is_valid(schema_id):
            raise HTTPException(status_code=400, detail="Invalid schema ID format")
        
        # Check if schema exists
        existing_schema = await schemas_collection.find_one({"_id": ObjectId(schema_id)})
        if not existing_schema:
            raise HTTPException(status_code=404, detail="Schema not found")
        
        if hard_delete:
            # Permanently delete the schema
            await schemas_collection.delete_one({"_id": ObjectId(schema_id)})
            message = "Schema permanently deleted"
        else:
            # Soft delete - mark as inactive
            await schemas_collection.update_one(
                {"_id": ObjectId(schema_id)},
                {"$set": {"active": False, "updated_at": datetime.utcnow()}}
            )
            message = "Schema deactivated"
        
        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schema: {str(e)}")


@router.post("/{schema_id}/activate")
async def activate_schema(
    schema_id: str,
    db = Depends(get_database)
):
    """Reactivate a deactivated schema"""
    try:
        schemas_collection = db.schemas
        
        # Validate ObjectId format
        if not ObjectId.is_valid(schema_id):
            raise HTTPException(status_code=400, detail="Invalid schema ID format")
        
        # Check if schema exists
        existing_schema = await schemas_collection.find_one({"_id": ObjectId(schema_id)})
        if not existing_schema:
            raise HTTPException(status_code=404, detail="Schema not found")
        
        # Activate the schema
        await schemas_collection.update_one(
            {"_id": ObjectId(schema_id)},
            {"$set": {"active": True, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": "Schema activated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate schema: {str(e)}")