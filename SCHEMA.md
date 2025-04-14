# Cassandra Schema for FB Messenger MVP

## 1. messages_by_conversation
```sql
CREATE TABLE IF NOT EXISTS messages_by_conversation (
    conversation_id UUID,
    sent_at TIMESTAMP,
    message_id UUID,
    sender_id INT,
    recipient_id INT,
    message_text TEXT,
    PRIMARY KEY ((conversation_id), sent_at, message_id)
) WITH CLUSTERING ORDER BY (sent_at DESC, message_id ASC);
```

## 2. conversations_by_user
```sql
CREATE TABLE IF NOT EXISTS conversations_by_user (
    user_id INT,
    last_activity TIMESTAMP,
    conversation_id UUID,
    participant_id INT,
    PRIMARY KEY ((user_id), last_activity, conversation_id)
) WITH CLUSTERING ORDER BY (last_activity DESC, conversation_id ASC);
```
