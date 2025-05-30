from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import argparse
import logging
from configuration import Config
from router import router, set_config
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global config
    set_config(config)
    app.include_router(router)
    app.mount("/", StaticFiles(directory=config.server.staticPath, html=True), name="static")
    yield

def main():
    parser = argparse.ArgumentParser(description="启动Web服务器")
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    args = parser.parse_args()

    # 加载配置
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            global config
            config = Config.model_validate_json(f.read())
    else:
        raise FileNotFoundError(f"配置文件 {args.config} 不存在")

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host=config.server.host, port=config.server.port)

if __name__ == '__main__':
    main()