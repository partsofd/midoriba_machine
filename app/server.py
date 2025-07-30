from threading import Thread

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
	return {"message": "Server is Online."}

@app.get("/health")
async def health_check():
	return {"status": "healthy", "message": "Discord Bot is running"}

def start():
	uvicorn.run(app, host="0.0.0.0", port=8080)

def server_thread():
	t = Thread(target=start)
	t.start()
