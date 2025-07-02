from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(50), unique=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    feedback_entries = relationship("FeedbackEntry", back_populates="product")

class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"))
    score = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    product = relationship("Product", back_populates="feedback_entries")