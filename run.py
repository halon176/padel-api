import uvicorn

from src.config import settings
from src.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port, reload=False, use_colors=True)
