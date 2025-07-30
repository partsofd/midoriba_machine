#!/usr/bin/env python3
"""
Koyeb環境でのシンプルな起動スクリプト
"""

import os
import sys
import time
import threading
from fastapi import FastAPI
import uvicorn

# FastAPIアプリケーションを作成
app = FastAPI(title="Discord Bot Health Check")

@app.get("/")
async def root():
    return {
        "message": "Discord Bot is running",
        "status": "online",
        "timestamp": time.time()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "Discord Bot is healthy",
        "timestamp": time.time()
    }

def start_fastapi():
    """FastAPIサーバーを起動"""
    try:
        print("🌐 Starting FastAPI server on port 8080...")
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    except Exception as e:
        print(f"❌ FastAPI server error: {e}")

def start_discord_bot():
    """Discord Botを起動"""
    try:
        print("🤖 Starting Discord Bot...")
        # main.pyの内容を実行
        import main
    except Exception as e:
        print(f"❌ Discord Bot error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Discord Bot with health check...")
    
    # 環境変数の確認
    token = os.environ.get("TOKEN")
    if not token:
        print("❌ TOKEN environment variable is not set")
        sys.exit(1)
    
    print(f"✅ TOKEN: {token[:10]}...")
    
    # FastAPIサーバーを別スレッドで起動
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()
    
    # 少し待機
    time.sleep(2)
    print("✅ FastAPI server started")
    
    # Discord Botを起動
    start_discord_bot() 