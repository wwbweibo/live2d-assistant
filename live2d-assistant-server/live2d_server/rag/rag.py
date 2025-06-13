import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader
)
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# Milvus imports  
from pymilvus import DataType, MilvusClient

# Other imports
from PIL import Image
import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusRAGSystem:
    """基于Milvus和LangChain的RAG系统"""
    def __init__(
        self,
        collection_name: str = "knowledge_base",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        db_path: str = "./milvus_lite.db",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.db_path = db_path
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "!", "?", "；", ")", "}", "]"]
        )
        
        # 初始化Milvus客户端（本地文件模式）
        self._init_milvus_client()
        
        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _init_milvus_client(self):
        """初始化Milvus客户端（本地文件模式）"""
        try:
            # 创建本地文件数据库目录
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # 初始化Milvus客户端（本地文件模式）
            self.client = MilvusClient(self.db_path)
            logger.info(f"Initialized Milvus client with local database: {self.db_path}")
            
            # 创建集合（如果不存在）
            self._create_collection_if_not_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize Milvus client: {e}")
            raise
    
    def _create_collection_if_not_exists(self):
        """创建Milvus集合（如果不存在）"""
        if self.client.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            return
        
        # 定义集合Schema（使用MilvusClient的简化API）
        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        
        # 添加字段
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=100, is_primary=True)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=384)
        schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=500)
        schema.add_field(field_name="file_id", datatype=DataType.VARCHAR, max_length=100)
        schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
        schema.add_field(field_name="metadata", datatype=DataType.VARCHAR, max_length=2000)
        
        # 创建索引参数
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 1024}
        )
        
        # 创建集合
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )
        
        logger.info(f"Created collection {self.collection_name}")
    
    async def process_file(self, file_path: str, file_id: str) -> Dict[str, Any]:
        """处理上传的文件"""
        try:
            # 根据文件类型选择加载器
            documents = await self._load_document(file_path)
            
            if not documents:
                return {
                    "status": "failed",
                    "error": "Failed to extract text from file"
                }
            
            # 分割文档
            chunks = self.text_splitter.split_documents(documents)
            
            # 生成向量并存储
            await self._store_chunks(chunks, file_id, file_path)
            
            # 提取文本内容用于前端显示
            full_text = "\n\n".join([doc.page_content for doc in documents])
            
            return {
                "status": "completed",
                "content": full_text,
                "chunks_count": len(chunks),
                "file_id": file_id
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _load_document(self, file_path: str) -> List[Document]:
        """根据文件类型加载文档"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return await self._load_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                return await self._load_docx(file_path)
            elif file_extension == '.txt':
                return await self._load_txt(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                return await self._load_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return []
    
    async def _load_pdf(self, file_path: str) -> List[Document]:
        """加载PDF文件"""
        loop = asyncio.get_event_loop()
        
        def _load():
            # 使用PyMuPDF进行更好的中文支持
            doc = fitz.open(file_path)
            documents = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "page": page_num + 1
                        }
                    ))
            
            doc.close()
            return documents
        
        return await loop.run_in_executor(self.executor, _load)
    
    async def _load_docx(self, file_path: str) -> List[Document]:
        """加载Word文档"""
        loop = asyncio.get_event_loop()
        
        def _load():
            loader = Docx2txtLoader(file_path)
            return loader.load()
        
        return await loop.run_in_executor(self.executor, _load)
    
    async def _load_txt(self, file_path: str) -> List[Document]:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [Document(
            page_content=content,
            metadata={"source": file_path}
        )]

    
    async def _load_image(self, file_path: str) -> List[Document]:
        """加载图片文件并进行OCR"""
        ocr = RapidOCR()  # RapidOCR 实例可复用
        image = Image.open(file_path)
        result, _ = ocr(image)
        text = "\n".join([line[1] for line in result]) if result else ""
        
        if text.strip():
            return [Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "type": "image_ocr"
                }
            )]
        else:
            return [Document(
                page_content="[图片文件，未检测到文字内容]",
                metadata={
                    "source": file_path,
                    "type": "image"
                }
            )]
    
    async def _store_chunks(self, chunks: List[Document], file_id: str, source: str):
        """将文档块存储到Milvus"""
        if not chunks:
            return
        
        # 准备数据
        entities = []
        
        for i, chunk in enumerate(chunks):
            # 生成唯一ID
            chunk_id = f"{file_id}_{i}"
            
            # 生成嵌入向量
            embedding = await self._generate_embedding(chunk.page_content)
            
            entities.append({
                "id": chunk_id,
                "text": chunk.page_content,
                "embedding": embedding,
                "source": source,
                "file_id": file_id,
                "chunk_index": i,
                "metadata": str(chunk.metadata)
            })
        
        # 批量插入到Milvus
        self.client.insert(
            collection_name=self.collection_name,
            data=entities
        )
        
        logger.info(f"Stored {len(entities)} chunks for file {file_id}")
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        loop = asyncio.get_event_loop()
        
        def _embed():
            return self.embeddings.embed_query(text)
        
        return await loop.run_in_executor(self.executor, _embed)
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            # 生成查询向量
            query_embedding = await self._generate_embedding(query)
            
            # 执行搜索
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                anns_field="embedding",
                search_params={"metric_type": "COSINE", "params": {"nprobe": 16}},
                limit=top_k,
                output_fields=["text", "source", "file_id", "chunk_index", "metadata"]
            )
            
            # 处理结果
            similar_docs = []
            for result in results[0]:  # results是一个列表，每个查询对应一个结果列表
                similar_docs.append({
                    "text": result["entity"]["text"],
                    "source": result["entity"]["source"],
                    "file_id": result["entity"]["file_id"],
                    "chunk_index": result["entity"]["chunk_index"],
                    "score": result["distance"],
                    "metadata": result["entity"]["metadata"]
                })
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    async def delete_file_chunks(self, file_id: str) -> bool:
        """删除文件的所有文档块"""
        try:
            # 根据file_id删除相关文档
            filter_expr = f'id == "{file_id}"'
            self.client.delete(
                collection_name=self.collection_name,
                filter=filter_expr
            )

            # 删除文件
            os.remove(file_id)
            logger.info(f"Deleted chunks for file {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file chunks: {e}")
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            # 查询文件的所有块
            filter_expr = f'file_id == "{file_id}"'
            results = self.client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=["text", "source", "chunk_index"]
            )
            
            if not results:
                return None
            
            # 组合文本内容
            chunks = sorted(results, key=lambda x: x["chunk_index"])
            full_text = "\n\n".join([chunk["text"] for chunk in chunks])
            
            return {
                "file_id": file_id,
                "content": full_text,
                "chunks_count": len(chunks),
                "source": chunks[0]["source"] if chunks else None
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
    
    async def rag_query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """RAG查询：检索相关文档并生成回答"""
        try:
            # 搜索相关文档
            similar_docs = await self.search_similar(query, top_k)
            
            if not similar_docs:
                return {
                    "answer": "抱歉，我在知识库中没有找到相关信息。",
                    "sources": [],
                    "query": query
                }
            
            # 构建上下文
            context_parts = []
            sources = []
            
            for doc in similar_docs:
                context_parts.append(doc["text"])
                sources.append({
                    "source": doc["source"],
                    "score": doc["score"],
                    "file_id": doc["file_id"]
                })
            
            context = "\n\n".join(context_parts)
            
            return {
                "context": context,
                "sources": sources,
                "query": query,
                "retrieved_docs": len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "answer": f"查询时发生错误: {str(e)}",
                "sources": [],
                "query": query
            }
    
    async def list_knowledge_base(self) -> List[Dict[str, Any]]:
        """列出知识库"""
        # 列出所有chunk，并返回文件名
        chunks = self.client.query(
            collection_name=self.collection_name,
            filter="",
            output_fields=["id", "metadata", "text"],
            limit=10000
        )
        logging.info(f"list_knowledge_base: {chunks}")
        return chunks

    def close(self):
        """关闭连接和资源"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
            self.executor.shutdown(wait=True)
            logger.info("RAG system closed")
        except Exception as e:
            logger.error(f"Error closing RAG system: {e}")

# 全局RAG系统实例
_rag_system = None

def get_rag_system() -> MilvusRAGSystem:
    """获取RAG系统实例（单例模式）"""
    global _rag_system
    if _rag_system is None:
        _rag_system = MilvusRAGSystem()
    return _rag_system

# 便捷函数
async def process_uploaded_file(file_path: str, file_id: str) -> Dict[str, Any]:
    """处理上传的文件"""
    rag_system = get_rag_system()
    return await rag_system.process_file(file_path, file_id)

async def list_knowledge_base() -> List[Dict[str, Any]]:
    """列出知识库"""
    rag_system = get_rag_system()
    return await rag_system.list_knowledge_base()

async def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """搜索知识库"""
    rag_system = get_rag_system()
    return await rag_system.search_similar(query, top_k)

async def query_with_rag(query: str, top_k: int = 3) -> Dict[str, Any]:
    """使用RAG进行查询"""
    rag_system = get_rag_system()
    return await rag_system.rag_query(query, top_k)

async def delete_knowledge_file(file_id: str) -> bool:
    """删除知识库文件"""
    rag_system = get_rag_system()
    return await rag_system.delete_file_chunks(file_id)

async def get_knowledge_file_info(file_id: str) -> Optional[Dict[str, Any]]:
    """获取知识库文件信息"""
    rag_system = get_rag_system()
    return await rag_system.get_file_info(file_id)

async def delete_knowledge_base(file_id: str) -> bool:
    """删除知识库文件"""
    rag_system = get_rag_system()
    return await rag_system.delete_file_chunks(file_id)
