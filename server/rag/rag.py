import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import (
    TextLoader,
    DirectoryLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    Docx2txtLoader
)

class RAGProcessor:
    def __init__(self, model_name="shibing624/text2vec-base-chinese"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
        )
        
    def load_documents(self, docs_dir: str) -> List:
        """加载目录下的多种文档格式（支持txt, md, pdf, docx）"""
        loaders = {
            'txt': DirectoryLoader(
                docs_dir, 
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf8'}
            ),
            'md': DirectoryLoader(
                docs_dir,
                glob="**/*.md",
                loader_cls=UnstructuredMarkdownLoader
            ),
            'pdf': DirectoryLoader(
                docs_dir,
                glob="**/*.pdf",
                loader_cls=UnstructuredPDFLoader
            ),
            'docx': DirectoryLoader(
                docs_dir,
                glob="**/*.docx",
                loader_cls=Docx2txtLoader
            )
        }
        
        documents = []
        for loader in loaders.values():
            documents.extend(loader.load())
        return documents
        
    def split_documents(self, documents: List) -> List:
        """将文档切分成小块"""
        return self.text_splitter.split_documents(documents)
        
    def create_vectorstore(self, documents: List, persist_dir: str = None) -> FAISS:
        """创建向量数据库"""
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
            vectorstore.save_local(persist_dir)
        return vectorstore
        
    def process_documents(self, docs_dir: str, persist_dir: str = None) -> FAISS:
        """处理文档的完整流程"""
        documents = self.load_documents(docs_dir)
        splits = self.split_documents(documents)
        vectorstore = self.create_vectorstore(splits, persist_dir)
        return vectorstore

    def load_vectorstore(self, persist_dir: str) -> FAISS:
        """从本地加载已存在的向量数据库"""
        if os.path.exists(persist_dir):
            return FAISS.load_local(persist_dir, self.embeddings)
        raise FileNotFoundError(f"向量数据库目录 {persist_dir} 不存在")
