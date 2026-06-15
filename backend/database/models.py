from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from backend.database.database import Base # ✅ FIXEDPATH HERE

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Input Data
    query_type = Column(String, index=True) # "text" or "image"
    food_name = Column(String, index=True)
    health_goal = Column(String)
    
    # AI Output Data
    calories = Column(Integer)
    protein_g = Column(Float)
    health_rating = Column(Float)
    rating_label = Column(String)
    primary_warning = Column(Text)
    
    # Timestamp
    scanned_at = Column(DateTime, default=datetime.utcnow)