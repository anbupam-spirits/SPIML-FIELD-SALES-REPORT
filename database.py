from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# --- Configuration ---
# Default to SQLite for local development. 
# To use Postgres, set env var: DATABASE_URL=postgresql://user:pass@localhost/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///field_sales.db")

# Ensure we use the correct dialect for invalid URLs (e.g. if simple 'starts with' check logic is needed later)
# For now, standard SQLAlchemy URL handling applies.

Base = declarative_base()

class StoreVisit(Base):
    __tablename__ = 'store_visits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_date = Column(Date, nullable=False)
    visit_time = Column(Time, nullable=False)
    sr_name = Column(String, nullable=False)
    store_name = Column(String, nullable=False)
    visit_type = Column(String, nullable=False)
    store_category = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    lead_type = Column(String, nullable=False)
    follow_up_date = Column(String, nullable=True) # Keeping as String to match form input flexibility or Date
    products = Column(String, nullable=False)
    order_details = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    maps_url = Column(String, nullable=True)
    location_recorded_answer = Column(String, nullable=False)
    image_data = Column(Text, nullable=False) # Base64 string
    created_at = Column(DateTime, default=datetime.now)

# --- Engine & Session ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def save_visit(data: dict):
    """
    Saves a visit dictionary to the database.
    Returns: (bool, message)
    """
    session = SessionLocal()
    try:
        # data["visit_date"] comes as a string 'YYYY-MM-DD' from app.py usually, 
        # but SQLAlchemy Date column expects a date object or valid ISO string.
        # We'll assume app.py passes standard python objects or we parse them here if needed.
        # Given app.py sends `current_date` as string from strftime, SQLA usually handles ISO strings for SQLite/Postgres.
        # But safest is to convert strictly or let SQLA handle it.
        
        # We need to map the list/dict from app.py to this model.
        # App.py currently uses a list `row_data`. We should change app.py to pass a dict
        # OR we map the list here. A dict is cleaner for the interface.
        
        visit = StoreVisit(
            visit_date=datetime.strptime(data['date'], "%Y-%m-%d").date(),
            visit_time=datetime.strptime(data['time'], "%H:%M:%S").time(),
            sr_name=data['sr_name'],
            store_name=data['store_name'],
            visit_type=data['visit_type'],
            store_category=data['store_category'],
            phone_number=data['phone'],
            lead_type=data['lead_type'],
            follow_up_date=data['follow_up_date'],
            products=data['products'],
            order_details=data['order_details'],
            latitude=float(data['latitude']) if data['latitude'] else None,
            longitude=float(data['longitude']) if data['longitude'] else None,
            maps_url=data['maps_url'],
            location_recorded_answer=data['location_recorded_answer'],
            image_data=data['image_data']
        )
        
        session.add(visit)
        session.commit()
        session.refresh(visit)
        return True, f"Saved with ID: {visit.id}"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
