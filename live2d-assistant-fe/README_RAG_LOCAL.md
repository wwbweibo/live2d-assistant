# 本地文件 RAG 系统

## 🎯 特性

✅ **完全本地化** - 无需外部数据库服务器  
✅ **零配置启动** - 开箱即用  
✅ **多格式支持** - PDF、Word、TXT、图片  
✅ **中文优化** - 智能分词和语义搜索  
✅ **轻量级部署** - 基于 Milvus Lite 本地文件数据库  

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行测试
```bash
python scripts/rag_example.py --test
```

### 3. 体验演示
```bash
python scripts/rag_example.py --demo
```

## 📁 数据库管理

### 查看数据库信息
```bash
python scripts/manage_knowledge_db.py info
```

### 备份数据库
```bash
python scripts/manage_knowledge_db.py backup
```

### 恢复数据库
```bash
python scripts/manage_knowledge_db.py restore --backup-path backups/knowledge_db_backup_20241201_120000
```

### 列出所有备份
```bash
python scripts/manage_knowledge_db.py list-backups
```

### 清空数据库
```bash
python scripts/manage_knowledge_db.py clear
```

## 🔧 API 使用

```python
from server.rag import (
    process_uploaded_file,
    search_knowledge_base,
    query_with_rag
)

# 处理文件
result = await process_uploaded_file("document.pdf", "file_001")

# 搜索相似文档
docs = await search_knowledge_base("人工智能", top_k=5)

# RAG 查询
answer = await query_with_rag("什么是机器学习？")
```

## 📊 配置说明

数据库文件位置：`./milvus_lite.db`
- 主数据文件：`milvus_lite.db`
- 元数据目录：`milvus_lite.db.meta/`

可通过修改 `server/rag.py` 中的 `db_path` 参数来改变存储位置：

```python
rag_system = MilvusRAGSystem(
    db_path="./custom_path/knowledge.db"  # 自定义路径
)
```

## 🎯 与前端集成

本地 RAG 系统与知识库管理前端组件完全兼容，支持：
- 文件上传和处理
- 实时状态更新
- 文档内容展示
- 智能搜索

## 💡 优势

1. **简单部署** - 无需 Docker 或外部服务
2. **便携性好** - 数据库文件可随项目移动
3. **性能稳定** - 无网络依赖，响应速度快
4. **易于维护** - 简单的文件系统操作

## 📝 注意事项

- 确保有足够的磁盘空间存储向量数据
- 定期备份重要的知识库数据
- 大型数据集建议监控系统内存使用情况
- 如需分布式部署，可考虑迁移到 Milvus 集群版本 