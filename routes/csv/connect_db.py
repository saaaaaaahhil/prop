from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from threading import Lock
from config import Config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Retry configuration
RETRY_WAIT = wait_exponential(multiplier=Config.RETRY_MULTIPLIER, min=Config.RETRY_MIN, max=Config.RETRY_MAX)
RETRY_ATTEMPTS = Config.RETRY_ATTEMPTS

# Global dictionary to store database engines
engines = {}
locks = {}

global_lock = Lock()

def get_lock(project_id):
    global global_lock, locks

    # Ensure thread safety while accessing locks dictionary
    with global_lock:
        if project_id not in locks:
            locks[project_id] = Lock()
        return locks[project_id]

@retry(stop=stop_after_attempt(RETRY_ATTEMPTS), wait=RETRY_WAIT, retry=retry_if_exception_type(Exception))
def get_engine(db_name):
    global engines

    with get_lock(db_name):
        # Check if engine already exists
        if db_name in engines:
            return engines[db_name]

        db_username = Config.POSTGRES_USER
        db_password = Config.POSTGRES_PASSWORD
        db_host = Config.POSTGRES_HOST
        db_port = Config.POSTGRES_PORT

        # Encode password for inclusion in URI
        encoded_password = quote_plus(db_password)

        # PostgreSQL connection string
        connection_str = f'postgresql://{db_username}:{encoded_password}@{db_host}:{db_port}/{db_name}'
        engine = create_engine(connection_str, pool_pre_ping=True)
        engines[db_name] = engine
        return engine

def get_or_create_database(project_id):
    with get_lock(project_id):
        if project_id in engines:
            print(f"Engine for {project_id} already exists.")
            return engines[project_id]

        default_db = Config.POSTGRES_DEFAULT_DB  # Typically 'postgres'
        engine = get_engine(default_db)

        # Connection in autocommit mode for operations that can't run in a transaction
        connection = engine.connect()
        connection.execution_options(isolation_level="AUTOCOMMIT")

        try:
            # Check if database already exists
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{project_id}'"))
            exists = result.fetchone()
            if not exists:
                # Create new database if it doesn't exist
                connection.execute(text(f"CREATE DATABASE {project_id}"))
                print(f"Database {project_id} created.")
            else:
                print(f"Database {project_id} already exists.")
        except SQLAlchemyError as e:
            print(f"Error creating database: {str(e)}")
            raise
        finally:
            connection.close()
            engine.dispose()

    # Return the engine connected to the newly created or existing database
    return get_engine(project_id)
