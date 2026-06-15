from __future__ import annotations

from pymongo.collection import Collection

from app.models.safety_log import SafetyLog


class SafetyLogRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def insert(self, safety_log: SafetyLog) -> SafetyLog:
        self.collection.insert_one(safety_log.model_dump(mode="python"))
        return safety_log
