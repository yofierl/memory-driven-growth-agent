"""Initialize local MongoDB indexes, Milvus collection, and MVP method seed data."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from dotenv import load_dotenv
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from pymongo import ASCENDING, MongoClient

METHODS = [
    {
        "method_id": "method_15_min_start",
        "name": "15 分钟启动法",
        "target_problem": ["拖延", "回避", "任务压力过大"],
        "difficulty": "low",
        "steps": ["选择一个最小任务", "设置 15 分钟", "只要求开始", "结束后记录感受"],
    },
    {
        "method_id": "method_cognitive_record",
        "name": "认知记录表",
        "target_problem": ["内耗", "反复想太多", "自我否定"],
        "difficulty": "low",
        "steps": ["写下事件", "写下自动想法", "写下情绪", "写下证据", "写下更平衡的解释"],
    },
    {
        "method_id": "method_attention_recovery",
        "name": "注意力回收训练",
        "target_problem": ["高敏感", "外界评价", "消息回复"],
        "difficulty": "low",
        "steps": ["识别关注对象", "判断是否有帮助", "减少非必要接触", "转回一个可完成动作"],
    },
    {
        "method_id": "method_meaning_writing",
        "name": "人生意义探索写作",
        "target_problem": ["长期迷茫", "人生方向", "职业目标"],
        "difficulty": "low",
        "steps": ["写下理想状态", "写下赚钱目的", "写下需要的能力", "反推当前阶段动作"],
    },
]


def init_mongo() -> None:
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGODB_DATABASE", "growth_agent")]

    db.users.create_index([("user_id", ASCENDING)], unique=True)
    db.conversations.create_index([("conversation_id", ASCENDING)], unique=True)
    db.conversations.create_index([("user_id", ASCENDING), ("updated_at", ASCENDING)])
    db.memories.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    db.memories.create_index([("user_id", ASCENDING), ("type", ASCENDING)])
    db.memories.create_index([("memory_id", ASCENDING)], unique=True)
    db.patterns.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
    db.patterns.create_index([("pattern_id", ASCENDING)], unique=True)
    db.tasks.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
    db.tasks.create_index([("task_id", ASCENDING)], unique=True)
    db.methods.create_index([("method_id", ASCENDING)], unique=True)

    now = datetime.now(UTC)
    for method in METHODS:
        db.methods.update_one(
            {"method_id": method["method_id"]},
            {
                "$set": {**method, "updated_at": now},
                "$setOnInsert": {"created_at": now},
                "$unset": {"tags": "", "complexity": ""},
            },
            upsert=True,
        )


def init_milvus() -> None:
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    collection_name = os.getenv("MILVUS_COLLECTION", "memory_embeddings")
    dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

    connections.connect(alias="default", host=host, port=port)
    if utility.has_collection(collection_name):
        Collection(collection_name).load()
        return

    fields = [
        FieldSchema(name="embedding_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
        FieldSchema(name="memory_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="scenario", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="created_at", dtype=DataType.INT64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
    ]
    schema = CollectionSchema(fields=fields, description="Memory semantic retrieval index")
    collection = Collection(name=collection_name, schema=schema)
    collection.create_index(
        field_name="embedding",
        index_params={
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64},
        },
    )
    collection.load()


def main() -> None:
    load_dotenv()
    init_mongo()
    init_milvus()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
