from app.models.cassandra_models import ConversationModel
from fastapi import HTTPException, status
import uuid

from app.schemas.conversation import ConversationResponse, PaginatedConversationResponse



class ConversationController:
    """
    Controller for handling conversation operations.
    """
    
    async def get_user_conversations(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 20
    ) -> PaginatedConversationResponse:
        """
        Get all conversations for a user with pagination.
        """
        try:
            conv_data = await ConversationModel.get_user_conversations(user_id, page, limit)
            return PaginatedConversationResponse(**conv_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationResponse:
        """
        Get a specific conversation by ID.
        """
        try:
            conv = await ConversationModel.get_conversation(conversation_id)
            return ConversationResponse(**conv)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
