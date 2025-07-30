from threading import Thread
import time
import logging

from fastapi import FastAPI
import uvicorn

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Discord Bot API", version="1.0.0")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Server is Online.", "status": "running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "message": "Discord Bot is running", "timestamp": time.time()}

@app.get("/ready")
async def ready_check():
    logger.info("Ready check endpoint accessed")
    return {"status": "ready", "message": "Application is ready to serve requests"}

def start():
    try:
        logger.info("Starting FastAPI server on port 8080...")
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        raise

def server_thread():
    try:
        logger.info("Creating server thread...")
        t = Thread(target=start, daemon=True)
        t.start()
        logger.info("Server thread started successfully")
    except Exception as e:
        logger.error(f"Failed to create server thread: {e}")
        raise