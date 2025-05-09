from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import argparse
import logging
from client import MCPClient, MCPClientConfig, MCPServerConfig, LLMConfig
from configuration import Config
from router import router, set_config, set_mcp_client
import asyncio
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_client = MCPClient(MCPClientConfig(
        llm=LLMConfig(
            provider=config.server.llm.provider,
            api_key=config.server.llm.api_key,
            base_url=config.server.llm.base_url,
            sys_prompt=config.server.llm.sys_prompt
        ),
        mcp_servers=[MCPServerConfig(
            name=server.name,
            transport=server.transport,
            url=server.url,
            command=server.command,
            args=server.args,
            env=server.env
        ) for server in config.server.mcp_servers]
    ))
    await mcp_client.connect_to_servers()
    tools = await mcp_client.list_all_tools()
    for tool in tools:
        print(tool)
    set_config(config)
    set_mcp_client(mcp_client)
    app.include_router(router)
    app.mount("/", StaticFiles(directory=config.server.staticPath, html=True), name="static")
    yield

parser = argparse.ArgumentParser(description="启动Web服务器")
parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
args = parser.parse_args()

# 加载配置
if os.path.exists(args.config):
    with open(args.config, 'r') as f:
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

if __name__ == '__main__':
    uvicorn.run(app, host=config.server.host, port=config.server.port)
    