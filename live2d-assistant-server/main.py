from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import argparse
import logging
from live2d_server.router import router
from live2d_server.rag.router import router as rag_router
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

static_path = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    app.include_router(router)
    app.include_router(rag_router)
    if static_path:
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
    yield

def main(app: FastAPI):
    parser = argparse.ArgumentParser(description="启动Web服务器")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机', required=False)
    parser.add_argument('--port', type=int, default=3000, help='服务器端口', required=False)
    parser.add_argument('--static-path', type=str, default=None, help='静态文件路径', required=False)
    args = parser.parse_args()
    global static_path
    static_path = args.static_path

    uvicorn.run(app, host=args.host, port=args.port)

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    main(app)