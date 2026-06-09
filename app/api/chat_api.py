from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pymongo import MongoClient

from app.agent.nodes.memory_extraction import MemoryExtractionNode
from app.agent.state import GrowthAgentState
from app.core.config import get_settings
from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.memory_repo import MemoryRepository
from app.repositories.user_repo import UserRepository
from app.schemas.chat_schema import ChatRequest, ChatResponse, SimpleChatResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_mongo_client(request: Request) -> MongoClient:
    client = getattr(request.app.state, "mongo_client", None)
    if client is None:
        settings = getattr(request.app.state, "settings", None)
        if settings is None:
            settings = get_settings()
            request.app.state.settings = settings
        client = MongoClient(settings.mongodb_uri)
        request.app.state.mongo_client = client
    return client


def get_user_repo(
    request: Request,
    client: Annotated[MongoClient, Depends(get_mongo_client)],
) -> UserRepository:
    override = getattr(request.app.state, "test_user_repo", None)
    if override is not None:
        return override
    db = client[request.app.state.settings.mongodb_database]
    return UserRepository(db.users)


def get_conversation_repo(
    request: Request,
    client: Annotated[MongoClient, Depends(get_mongo_client)],
) -> ConversationRepository:
    override = getattr(request.app.state, "test_conversation_repo", None)
    if override is not None:
        return override
    db = client[request.app.state.settings.mongodb_database]
    return ConversationRepository(db.conversations)


def get_memory_repo(
    request: Request,
    client: Annotated[MongoClient, Depends(get_mongo_client)],
) -> MemoryRepository:
    override = getattr(request.app.state, "test_memory_repo", None)
    if override is not None:
        return override
    db = client[request.app.state.settings.mongodb_database]
    return MemoryRepository(db.memories)


def get_llm_service(request: Request) -> LLMService:
    override = getattr(request.app.state, "test_llm_service", None)
    if override is not None:
        return override
    settings = getattr(request.app.state, "settings", None) or get_settings()
    request.app.state.settings = settings
    return LLMService(settings=settings)


@router.post("", response_model=ChatResponse)
async def chat(_: ChatRequest) -> ChatResponse:
    raise NotImplementedError("Phase 1 does not implement /api/chat yet")


@router.post("/simple", response_model=SimpleChatResponse)
async def simple_chat(
    request: ChatRequest,
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    conversation_repo: Annotated[
        ConversationRepository,
        Depends(get_conversation_repo),
    ],
    memory_repo: Annotated[MemoryRepository, Depends(get_memory_repo)],
) -> SimpleChatResponse:
    conversation_id = request.conversation_id or str(uuid4())
    existing_user = user_repo.get_by_user_id(request.user_id)
    if existing_user is None:
        user_repo.upsert(User(user_id=request.user_id))

    conversation = conversation_repo.get_by_conversation_id(conversation_id)
    if conversation is None:
        conversation = Conversation(conversation_id=conversation_id, user_id=request.user_id)

    user_message = ConversationMessage(role="user", content=request.message)
    conversation.messages.append(user_message)
    history_messages = [
        message.model_dump(mode="json") for message in conversation.messages[:-1]
    ]
    assistant_response = llm_service.generate_reply(
        user_message=request.message,
        conversation_messages=history_messages,
    )
    assistant_message = ConversationMessage(role="assistant", content=assistant_response)
    conversation.messages.append(assistant_message)
    conversation.updated_at = datetime.now(UTC)
    conversation_repo.save(conversation)

    state = GrowthAgentState(
        user_id=request.user_id,
        conversation_id=conversation_id,
        user_input=request.message,
        assistant_response=assistant_response,
    )
    extraction_node = MemoryExtractionNode(llm_service=llm_service)
    updated_state = extraction_node.run(state)
    stored_memories = memory_repo.create_many(updated_state.new_memories)
    memory_payloads = [memory.model_dump(mode="json") for memory in stored_memories]

    return SimpleChatResponse(
        conversation_id=conversation_id,
        assistant_response=assistant_response,
        strategy="simple_chat",
        stored_memory_count=len(stored_memories),
        memories=memory_payloads,
    )
