from __future__ import annotations

from pymongo.collection import Collection

from app.models.method import Method


class MethodRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def list_all(self) -> list[Method]:
        cursor = self.collection.find({}).sort("name", 1)
        return [self._to_model(document) for document in cursor]

    def get_by_method_id(self, method_id: str) -> Method | None:
        document = self.collection.find_one({"method_id": method_id})
        return self._to_model(document) if document else None

    @staticmethod
    def _to_model(document: dict | None) -> Method:
        assert document is not None
        document.pop("_id", None)
        return Method.model_validate(document)
