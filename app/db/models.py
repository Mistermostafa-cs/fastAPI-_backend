from app.db.entities import Base
from app.db.new_entities import Term, SubjectOffering  # registers new tables  # noqa: F401
from app.db.session import engine


def prepare_models() -> None:
    # Creates all tables (old + new) if they don't already exist
    Base.metadata.create_all(bind=engine)
