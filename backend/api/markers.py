from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from ..models.marker import Marker
from ..services import marker_service

router = APIRouter()

@router.post("/", response_description="Add new marker", response_model=Marker, status_code=status.HTTP_201_CREATED)
async def create_marker(marker: Marker = Body(...)):
    new_marker = await marker_service.create_marker(marker)
    return new_marker

@router.get("/", response_description="List all markers", response_model=List[Marker])
async def list_markers(skip: int = 0, limit: int = 100):
    markers = await marker_service.list_markers(skip, limit)
    return markers

@router.get("/{marker_id}", response_description="Get a single marker", response_model=Marker)
async def show_marker(marker_id: str):
    marker = await marker_service.get_marker(marker_id)
    if marker is not None:
        return marker
    raise HTTPException(status_code=404, detail=f"Marker {marker_id} not found")