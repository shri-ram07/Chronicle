"""
CHRONICLE - Run the server
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("Starting CHRONICLE server...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
