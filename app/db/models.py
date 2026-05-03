from app.db.entities import Base
from app.db.session import engine

def prepare_models() -> None:
    # This creates all tables in the database if they don't exist
    # Perfect for a standalone SQLite database
    Base.metadata.create_all(bind=engine)
