"""
MongoDB implementation of marker repository.
Handles all marker data access operations.
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from ..core.interfaces import IMarkerRepository
from ..core.exceptions import DatabaseError, MarkerNotFoundError
from ..core.logging import get_logger
from ..database import db
from ..models.marker import Marker

logger = get_logger(__name__)


class MongoMarkerRepository(IMarkerRepository):
    """MongoDB implementation of marker repository."""
    
    def __init__(self):
        """Initialize repository with database collection."""
        self.collection: AsyncIOMotorCollection = db["markers"]
        logger.info("Initialized MongoMarkerRepository")
    
    async def get_marker(self, marker_id: str) -> Optional[Marker]:
        """Get a single marker by ID."""
        try:
            marker_data = await self.collection.find_one({"_id": marker_id})
            if not marker_data:
                return None
            
            return Marker(**marker_data)
            
        except Exception as e:
            logger.error(f"Error getting marker {marker_id}: {str(e)}")
            raise DatabaseError(f"Failed to get marker: {str(e)}", "get_marker")
    
    async def list_markers(self, 
                          skip: int = 0, 
                          limit: int = 100,
                          schema_id: Optional[str] = None) -> List[Marker]:
        """List markers with pagination and filtering."""
        try:
            query = {}
            if schema_id:
                query["schema_id"] = schema_id
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            markers = []
            
            async for marker_data in cursor:
                try:
                    markers.append(Marker(**marker_data))
                except Exception as e:
                    logger.warning(f"Skipping invalid marker {marker_data.get('_id')}: {str(e)}")
            
            logger.info(f"Listed {len(markers)} markers (skip={skip}, limit={limit})")
            return markers
            
        except Exception as e:
            logger.error(f"Error listing markers: {str(e)}")
            raise DatabaseError(f"Failed to list markers: {str(e)}", "list_markers")
    
    async def create_marker(self, marker: Marker) -> Marker:
        """Create a new marker."""
        try:
            marker_dict = marker.model_dump(by_alias=True)
            await self.collection.insert_one(marker_dict)
            
            logger.info(f"Created marker {marker.id}")
            return marker
            
        except Exception as e:
            logger.error(f"Error creating marker: {str(e)}")
            raise DatabaseError(f"Failed to create marker: {str(e)}", "create_marker")
    
    async def update_marker(self, marker_id: str, marker: Marker) -> Optional[Marker]:
        """Update an existing marker."""
        try:
            # Ensure the ID matches
            if marker.id != marker_id:
                raise ValueError("Marker ID mismatch")
            
            marker_dict = marker.model_dump(by_alias=True)
            result = await self.collection.replace_one(
                {"_id": marker_id},
                marker_dict
            )
            
            if result.matched_count == 0:
                return None
            
            logger.info(f"Updated marker {marker_id}")
            return marker
            
        except Exception as e:
            logger.error(f"Error updating marker {marker_id}: {str(e)}")
            raise DatabaseError(f"Failed to update marker: {str(e)}", "update_marker")
    
    async def delete_marker(self, marker_id: str) -> bool:
        """Delete a marker."""
        try:
            result = await self.collection.delete_one({"_id": marker_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted marker {marker_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting marker {marker_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete marker: {str(e)}", "delete_marker")
    
    async def get_markers_by_type(self, marker_type: str) -> List[Marker]:
        """Get all markers of a specific type (A_, S_, C_, MM_)."""
        try:
            valid_types = ["A_", "S_", "C_", "MM_"]
            if marker_type not in valid_types:
                raise ValueError(f"Invalid marker type: {marker_type}")
            
            query = {"_id": {"$regex": f"^{marker_type}"}}
            cursor = self.collection.find(query)
            markers = []
            
            async for marker_data in cursor:
                try:
                    markers.append(Marker(**marker_data))
                except Exception as e:
                    logger.warning(f"Skipping invalid marker {marker_data.get('_id')}: {str(e)}")
            
            logger.info(f"Found {len(markers)} markers of type {marker_type}")
            return markers
            
        except Exception as e:
            logger.error(f"Error getting markers by type {marker_type}: {str(e)}")
            raise DatabaseError(f"Failed to get markers by type: {str(e)}", "get_markers_by_type")
    
    async def count_markers(self, schema_id: Optional[str] = None) -> int:
        """Count total markers, optionally filtered by schema."""
        try:
            query = {}
            if schema_id:
                query["schema_id"] = schema_id
            
            count = await self.collection.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Error counting markers: {str(e)}")
            raise DatabaseError(f"Failed to count markers: {str(e)}", "count_markers")
    
    async def get_marker_schemas(self) -> List[str]:
        """Get list of unique schema IDs."""
        try:
            schemas = await self.collection.distinct("schema_id")
            return [s for s in schemas if s]  # Filter out None/empty values
            
        except Exception as e:
            logger.error(f"Error getting marker schemas: {str(e)}")
            raise DatabaseError(f"Failed to get schemas: {str(e)}", "get_marker_schemas")