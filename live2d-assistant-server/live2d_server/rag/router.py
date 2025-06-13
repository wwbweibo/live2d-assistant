from fastapi import APIRouter
from fastapi import Form, File, UploadFile
import os
import logging
from live2d_server.rag.rag import process_uploaded_file, search_knowledge_base, list_knowledge_base, delete_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/rag', tags=['RAG'])

@router.post('/upload')
async def upload_rag(file_name: str = Form(...), file_data: UploadFile = File(...)):
    '''
    上传RAG
    '''
    logger.info(f"upload_rag: {file_name}")
    logger.info(f"upload_rag: {file_data}")
    if not os.path.exists("cache"):
        os.makedirs("cache")
    # 先写入本地文件
    with open( "cache/" + file_name, 'wb') as f:
        f.write(await file_data.read())
    # 写入 RAG
    await process_uploaded_file("cache/" + file_name, file_name)
    return {'status': 'OK'}

@router.get('/list')
async def list_rag():
    '''
    列出RAG
    '''
    return await list_knowledge_base()

@router.get('/search')
async def search_rag(query: str):
    '''
    搜索RAG
    '''
    return await search_knowledge_base(query)

@router.delete('/delete/{file_id}')
async def delete_rag(file_id: str):
    '''
    删除RAG
    '''
    return await delete_knowledge_base(file_id)