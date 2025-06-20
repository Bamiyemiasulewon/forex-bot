from sqlalchemy import text
from sqlalchemy.orm import Session

# Perform a health check on the database connection.
def db_health_check(db: Session):
    try:
        db.execute(text('SELECT 1'))
        return True
    except Exception:
        return False 