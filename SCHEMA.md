# Cassandra Schema for FB Messenger MVP

## 1. messages_by_conversation
```sql
CREATE TABLE IF NOT EXISTS messages_by_conversation (
    conversation_id UUID,
    sent_at TIMESTAMP,
    message_id UUID,
    sender_id INT,
    receiver_id INT,
    content TEXT,
    PRIMARY KEY ((conversation_id), sent_at, message_id)
) WITH CLUSTERING ORDER BY (sent_at DESC, message_id ASC);
```

## 2. conversations
```sql
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY,
    list_of_users LIST<INT>,
    last_message_content TEXT,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP
);
```
