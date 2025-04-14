"""
Script to initialize Cassandra keyspace and tables for the Messenger application.
"""
import os
import time
import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cassandra connection settings
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "messenger")

def wait_for_cassandra():
    """Wait for Cassandra to be ready before proceeding."""
    logger.info("Waiting for Cassandra to be ready...")
    cluster = None
    
    for _ in range(10):  # Try 10 times
        try:
            cluster = Cluster([CASSANDRA_HOST])
            session = cluster.connect()
            logger.info("Cassandra is ready!")
            return cluster
        except Exception as e:
            logger.warning(f"Cassandra not ready yet: {str(e)}")
            time.sleep(5)  # Wait 5 seconds before trying again
    
    logger.error("Failed to connect to Cassandra after multiple attempts.")
    raise Exception("Could not connect to Cassandra")

def create_keyspace(session):
    """
    Create the keyspace if it doesn't exist.
    
    This is where students will define the keyspace configuration.
    """
    logger.info(f"Creating keyspace {CASSANDRA_KEYSPACE} if it doesn't exist...")
    
    session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE} 
    WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }};
    """)
    session.set_keyspace(CASSANDRA_KEYSPACE)
    
    logger.info(f"Keyspace {CASSANDRA_KEYSPACE} is ready.")

def create_tables(session):
    """
    Create the tables for the application.
    
    This is where students will define the table schemas based on the requirements.
    """
    logger.info("Creating tables...")
    
    # TODO: Students should implement table creation
    # Hint: Consider:
    # - What tables are needed to implement the required APIs?
    # - What should be the primary keys and clustering columns?
    # - How will you handle pagination and time-based queries?
    session.execute("""
    CREATE TABLE IF NOT EXISTS messages_by_conversation (
        conversation_id UUID,
        sent_at TIMESTAMP,
        message_id UUID,
        sender_id INT,
        recipient_id INT,
        message_text TEXT,
        PRIMARY KEY ((conversation_id), sent_at, message_id)
    ) WITH CLUSTERING ORDER BY (sent_at DESC, message_id ASC);
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS conversations_by_user (
        user_id INT,
        last_activity TIMESTAMP,
        conversation_id UUID,
        participant_id INT,
        PRIMARY KEY ((user_id), last_activity, conversation_id)
    ) WITH CLUSTERING ORDER BY (last_activity DESC, conversation_id ASC);
    """)

    
    logger.info("Tables created successfully.")

def main():
    """Initialize the database."""
    logger.info("Starting Cassandra initialization...")
    
    # Wait for Cassandra to be ready
    cluster = wait_for_cassandra()
    
    try:
        # Connect to the server
        session = cluster.connect()
        
        # Create keyspace and tables
        create_keyspace(session)
        session.set_keyspace(CASSANDRA_KEYSPACE)
        create_tables(session)
        
        logger.info("Cassandra initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise
    finally:
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    main() 