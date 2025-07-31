from ..database import db
from pydantic import BaseModel

class HealthStatus(BaseModel):
    api_status: str = "ok"
    database_connected: bool

async def check_health() -> HealthStatus:
    try:
        await db.command("ping")
        return HealthStatus(database_connected=True)
    except Exception:
        return HealthStatus(database_connected=False)