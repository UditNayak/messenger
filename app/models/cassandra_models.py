"""
Sample models for interacting with Cassandra tables.
Students should implement these models based on their database schema design.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.cassandra_client import cassandra_client
from app.schemas.message import MessageResponse


class MessageModel:
    """
    Message model for interacting with the messages table.
    
    Considerations:
    - Efficient inserts into the messages_by_conversation table.
    - Basic pagination implemented by slicing the results list (not recommended for large datasets).
    - Filtering by timestamp is provided via the clustering column.
    """
    
    @staticmethod
    async def create_message(
        conversation_id: uuid.UUID,
        sender_id: int,
        receiver_id: int,
        content: str,
    ) -> Dict[str, Any]:
        """
        Create a new message and update conversation info.
        Inserts a new row into the messages_by_conversation table and updates the conversation.
        """
        created_at = datetime.utcnow()
        message_id = uuid.uuid4()
        # Insert message into the messages_by_conversation table.
        query = """
            INSERT INTO messages_by_conversation 
            (conversation_id, sent_at, message_id, sender_id, receiver_id, content)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (conversation_id, created_at, message_id, sender_id, receiver_id, content)
        cassandra_client.execute(query, params)
        
        # Update the conversation with the last message details.
        query_conv = """
            UPDATE conversations 
            SET last_message_content = %s, last_message_at = %s 
            WHERE conversation_id = %s
        """
        params_conv = (content, created_at, conversation_id)
        cassandra_client.execute(query_conv, params_conv)
        
        return {
            "id": message_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "created_at": created_at,
            "conversation_id": conversation_id,
        }
    
    @staticmethod
    async def get_conversation_messages(
        conversation_id: uuid.UUID, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get messages for a conversation with pagination.
        Note: This demo fetches all rows matching the conversation_id and then slices.
        This approach is acceptable for small volumes; for larger datasets consider using Cassandra paging state.
        """
        query = "SELECT * FROM messages_by_conversation WHERE conversation_id = %s"
        params = (conversation_id,)
        results = cassandra_client.execute(query, params)
        
        # Manual pagination: calculate slice indices.
        total = len(results)
        start = (page - 1) * limit
        paginated_results = results[start:start + limit]
        print("paginated_results", paginated_results)
        data = [
            MessageResponse(
                id=msg["message_id"],
                created_at=msg["sent_at"],
                sender_id=msg["sender_id"],
                receiver_id=msg["receiver_id"],
                content=msg["content"],
                conversation_id=msg["conversation_id"],
            )
            for msg in paginated_results
        ]

        return {"total": total, "page": page, "limit": limit, "data": data}
    
    @staticmethod
    async def get_messages_before_timestamp(
        conversation_id: uuid.UUID, before_timestamp: datetime, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get messages before the given timestamp, paginated.
        """
        query = """
            SELECT * FROM messages_by_conversation 
            WHERE conversation_id = %s AND sent_at < %s
        """
        params = (conversation_id, before_timestamp)
        results = cassandra_client.execute(query, params)
        
        total = len(results)
        start = (page - 1) * limit
        paginated_results = results[start:start + limit]

        data = [
            {
                "id": msg["message_id"],
                "created_at": msg["sent_at"],
                "sender_id": msg["sender_id"],
                "receiver_id": msg["receiver_id"],
                "content": msg["content"],
                "conversation_id": msg["conversation_id"],
            }
            for msg in paginated_results
        ]

        return {"total": total, "page": page, "limit": limit, "data": data}


class ConversationModel:
    """
    Conversation model for interacting with the conversations-related table.
    
    Considerations:
    - Retrieving conversations for a user (using ALLOW FILTERING) may not scale,
      so in a production system a dedicated table or secondary indexes might be preferred.
    - For simplicity we assume a conversation between two users contains exactly two IDs.
    """
    
    @staticmethod
    async def get_user_conversations(
        user_id: int, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get conversations for a user with pagination.
        We use filtering with ALLOW FILTERING on the list_of_users field.
        """
        query = "SELECT * FROM conversations WHERE list_of_users CONTAINS %s ALLOW FILTERING"
        params = (user_id,)
        results = cassandra_client.execute(query, params)
        
        # Sort by last_message_at descending.
        results.sort(key=lambda x: x.get("last_message_at") or datetime.min, reverse=True)
        total = len(results)
        start = (page - 1) * limit
        data = results[start:start + limit]
        
        conv_list = []
        for conv in data:
            # Assume list_of_users has at least two elements. We sort them to get consistent ordering.
            users = conv.get("list_of_users", [])
            if len(users) >= 2:
                user1, user2 = sorted(users)[:2]
            elif len(users) == 1:
                user1 = user2 = users[0]
            else:
                user1 = user2 = None
            conv_list.append({
                "id": conv["conversation_id"],
                "user1_id": user1,
                "user2_id": user2,
                "last_message_at": conv["last_message_at"],
                "last_message_content": conv.get("last_message_content")
            })
        
        return {"total": total, "page": page, "limit": limit, "data": conv_list}
    
    @staticmethod
    async def get_conversation(conversation_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get a conversation by ID.
        """
        query = "SELECT * FROM conversations WHERE conversation_id = %s"
        params = (conversation_id,)
        results = cassandra_client.execute(query, params)
        if not results:
            raise Exception("Conversation not found")
        
        conv = results[0]
        users = conv.get("list_of_users", [])
        if len(users) >= 2:
            user1, user2 = sorted(users)[:2]
        elif len(users) == 1:
            user1 = user2 = users[0]
        else:
            user1 = user2 = None
        
        return {
            "id": conv["conversation_id"],
            "user1_id": user1,
            "user2_id": user2,
            "last_message_at": conv["last_message_at"],
            "last_message_content": conv.get("last_message_content")
        }
    
    @staticmethod
    async def create_or_get_conversation(
        user1_id: int, user2_id: int
    ) -> Dict[str, Any]:
        """
        Get an existing conversation between two users or create a new one.
        
        Since the conversations table uses only conversation_id as the primary key,
        we scan for a conversation where user1 is in the list_of_users and then check if user2 is also present.
        """
        query = "SELECT * FROM conversations WHERE list_of_users CONTAINS %s ALLOW FILTERING"
        params = (user1_id,)
        results = cassandra_client.execute(query, params)
        
        for conv in results:
            if user2_id in conv.get("list_of_users", []):
                return conv
        
        # No conversation exists: create a new conversation.
        conversation_id = uuid.uuid4()
        created_at = datetime.utcnow()
        query_insert = """
            INSERT INTO conversations 
            (conversation_id, list_of_users, created_at, last_message_at)
            VALUES (%s, %s, %s, %s)
        """
        params_insert = (conversation_id, [user1_id, user2_id], created_at, created_at)
        cassandra_client.execute(query_insert, params_insert)
        
        return {
            "id": conversation_id,
            "user1_id": min(user1_id, user2_id),
            "user2_id": max(user1_id, user2_id),
            "created_at": created_at,
            "last_message_at": created_at,
            "last_message_content": None,
            "list_of_users": [user1_id, user2_id]
        }
