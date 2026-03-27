"""
配置存储模块，使用 SQLite 持久化 LLM、Agent 和 Skill 配置。
"""

import json
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "./.config.db"


def get_db_path() -> str:
    """获取数据库路径"""
    return os.path.join(os.path.dirname(__file__), "..", DB_PATH)


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    db_file = get_db_path()
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # LLM 配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                provider TEXT NOT NULL DEFAULT 'openai_compatible',
                api_key TEXT,
                model TEXT NOT NULL DEFAULT 'qwen2.5',
                base_url TEXT
            )
        """)
        # Agent 配置表 — 存储完整的 AgentConfig JSON（单行）
        # 检查旧表结构，如果不兼容则重建
        cursor.execute("PRAGMA table_info(agents_config)")
        columns = {row["name"] for row in cursor.fetchall()}
        if columns and "config" not in columns:
            # 旧表结构（name/duty/skills...），删除重建
            cursor.execute("DROP TABLE agents_config")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config TEXT NOT NULL DEFAULT '{}'
            )
        """)
        # 插入默认 LLM 配置（如果不存在）
        cursor.execute("SELECT COUNT(*) FROM llm_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO llm_config (id, provider, api_key, model, base_url)
                VALUES (1, 'openai_compatible', '', 'qwen2.5', 'http://localhost:11434/v1')
            """)
        # 插入默认 Agent 配置（如果不存在）
        cursor.execute("SELECT COUNT(*) FROM agents_config")
        if cursor.fetchone()[0] == 0:
            default_config = json.dumps({
                "metadata": {},
                "agents": [],
                "mcp_servers": [],
            })
            cursor.execute(
                "INSERT INTO agents_config (id, config) VALUES (1, ?)",
                (default_config,),
            )
        # Skills 配置表 — 存储 SkillMeta 列表 JSON（单行）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config TEXT NOT NULL DEFAULT '[]'
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM skills_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO skills_config (id, config) VALUES (1, ?)",
                (json.dumps([]),),
            )
        # MCP Server 配置表 — 存储 MCPServerConfig 列表 JSON（单行）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_servers_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config TEXT NOT NULL DEFAULT '[]'
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM mcp_servers_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO mcp_servers_config (id, config) VALUES (1, ?)",
                (json.dumps([]),),
            )


def get_llm_config() -> dict:
    """获取 LLM 配置"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT provider, api_key, model, base_url FROM llm_config WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "provider": row["provider"],
                "api_key": row["api_key"] or "",
                "model": row["model"],
                "base_url": row["base_url"]
            }
        return {
            "provider": "openai_compatible",
            "api_key": "",
            "model": "qwen2.5",
            "base_url": "http://localhost:11434/v1"
        }


def update_llm_config(config: dict) -> dict:
    """更新 LLM 配置"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE llm_config
            SET provider = ?, api_key = ?, model = ?, base_url = ?
            WHERE id = 1
        """, (config["provider"], config["api_key"], config["model"], config["base_url"]))
    return config


def get_agents_config() -> dict:
    """获取完整的 AgentConfig（metadata + agents + mcp_servers）"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT config FROM agents_config WHERE id = 1")
        row = cursor.fetchone()
        if row and row["config"]:
            return json.loads(row["config"])
        return {"metadata": {}, "agents": [], "mcp_servers": []}


def update_agents_config(config: dict) -> dict:
    """更新完整的 AgentConfig"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE agents_config SET config = ? WHERE id = 1",
            (json.dumps(config, ensure_ascii=False),),
        )
    return config


def delete_agent_by_name(name: str) -> bool:
    """从 AgentConfig 中删除指定名称的 Agent"""
    config = get_agents_config()
    original_len = len(config.get("agents", []))
    config["agents"] = [a for a in config.get("agents", []) if a.get("name") != name]
    if len(config["agents"]) < original_len:
        update_agents_config(config)
        return True
    return False


# ─── Skills 配置 ─────────────────────────────────


def get_skills_config() -> list[dict]:
    """获取所有 SkillMeta 列表"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT config FROM skills_config WHERE id = 1")
        row = cursor.fetchone()
        if row and row["config"]:
            return json.loads(row["config"])
        return []


def update_skills_config(skills: list[dict]) -> list[dict]:
    """整体更新 SkillMeta 列表"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE skills_config SET config = ? WHERE id = 1",
            (json.dumps(skills, ensure_ascii=False),),
        )
    return skills


def upsert_skill(skill: dict) -> dict:
    """新增或更新单个 Skill（按 name 匹配）"""
    skills = get_skills_config()
    idx = next((i for i, s in enumerate(skills) if s.get("name") == skill["name"]), None)
    if idx is not None:
        skills[idx] = skill
    else:
        skills.append(skill)
    update_skills_config(skills)
    return skill


def delete_skill_by_name(name: str) -> bool:
    """删除指定名称的 Skill"""
    skills = get_skills_config()
    original_len = len(skills)
    skills = [s for s in skills if s.get("name") != name]
    if len(skills) < original_len:
        update_skills_config(skills)
        return True
    return False


# ─── MCP Server 配置 ─────────────────────────────


def get_mcp_servers_config() -> list[dict]:
    """获取所有 MCPServerConfig 列表"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT config FROM mcp_servers_config WHERE id = 1")
        row = cursor.fetchone()
        if row and row["config"]:
            return json.loads(row["config"])
        return []


def update_mcp_servers_config(servers: list[dict]) -> list[dict]:
    """整体更新 MCPServerConfig 列表"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE mcp_servers_config SET config = ? WHERE id = 1",
            (json.dumps(servers, ensure_ascii=False),),
        )
    return servers


def upsert_mcp_server(server: dict) -> dict:
    """新增或更新单个 MCP Server（按 name 匹配）"""
    servers = get_mcp_servers_config()
    idx = next((i for i, s in enumerate(servers) if s.get("name") == server["name"]), None)
    if idx is not None:
        servers[idx] = server
    else:
        servers.append(server)
    update_mcp_servers_config(servers)
    return server


def delete_mcp_server_by_name(name: str) -> bool:
    """删除指定名称的 MCP Server"""
    servers = get_mcp_servers_config()
    original_len = len(servers)
    servers = [s for s in servers if s.get("name") != name]
    if len(servers) < original_len:
        update_mcp_servers_config(servers)
        return True
    return False
