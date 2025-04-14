from typing import Optional
from datetime import datetime
import uuid

from app.models.cassandra_models import ConversationModel, MessageModel
from fastapi import HTTPException, status

from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessageResponse



class MessageController:
    """
    Controller for handling message operations.
    """
    
    async def send_message(self, message_data: MessageCreate) -> MessageResponse:
        """
        Send a message from one user to another.
        """
        try:
            # Retrieve or create a conversation between sender and receiver.
            conversation = await ConversationModel.create_or_get_conversation(
                message_data.sender_id, message_data.receiver_id
            )
            # Get conversation_id (the model returns key "id").
            conversation_id = conversation.get("id") or conversation.get("conversation_id")
            msg = await MessageModel.create_message(
                conversation_id, message_data.sender_id, message_data.receiver_id, message_data.content
            )
            return MessageResponse(**msg)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    async def get_conversation_messages(
        self, 
        conversation_id: uuid.UUID, 
        page: int = 1, 
        limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get all messages in a conversation with pagination.
        """
        try:
            messages_paginated = await MessageModel.get_conversation_messages(conversation_id, page, limit)
            return PaginatedMessageResponse(**messages_paginated)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    async def get_messages_before_timestamp(
        self, 
        conversation_id: uuid.UUID, 
        before_timestamp: datetime,
        page: int = 1, 
        limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get messages in a conversation before a specific timestamp with pagination.
        """
        try:
            messages_paginated = await MessageModel.get_messages_before_timestamp(conversation_id, before_timestamp, page, limit)
            return PaginatedMessageResponse(**messages_paginated)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
