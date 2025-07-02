from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
from datetime import datetime
# Import our modules
from database import engine, get_db
from models import Base, Product, FeedbackEntry

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Customer Feedback API", version="1.0.0")

# Pydantic schemas (keeping them simple in main file)
class FeedbackCreate(BaseModel):
    product_id: str
    score: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    product_id: str
    score: float
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductAverage(BaseModel):
    product_id: str
    average_score: float
    feedback_count: int

# Routes
@app.get("/")
def home():
    return {"message": "Feedback API is running!", "docs": "/docs"}

@app.post("/feedback/", response_model=FeedbackResponse)
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Create new feedback entry"""
    
    # Create product if doesn't exist
    product = db.query(Product).filter(Product.product_id == feedback.product_id).first()
    if not product:
        product = Product(product_id=feedback.product_id, name=f"Product {feedback.product_id}")
        db.add(product)
        db.commit()
    
    # Create feedback
    db_feedback = FeedbackEntry(
        product_id=feedback.product_id,
        score=feedback.score,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback

@app.get("/feedback/", response_model=List[FeedbackResponse])
def get_all_feedback(db: Session = Depends(get_db)):
    """Get all feedback entries"""
    feedback = db.query(FeedbackEntry).all()
    return feedback

@app.get("/feedback/averages/", response_model=List[ProductAverage])
def get_product_averages(db: Session = Depends(get_db)):
    """Get average scores for all products"""
    
    results = db.query(
        FeedbackEntry.product_id,
        func.avg(FeedbackEntry.score).label('average_score'),
        func.count(FeedbackEntry.id).label('feedback_count')
    ).group_by(FeedbackEntry.product_id).all()
    
    return [
        ProductAverage(
            product_id=result.product_id,
            average_score=round(float(result.average_score), 2),
            feedback_count=result.feedback_count
        )
        for result in results
    ]

@app.get("/feedback/product/{product_id}", response_model=List[FeedbackResponse])
def get_feedback_by_product(product_id: str, db: Session = Depends(get_db)):
    """Get feedback for specific product"""
    feedback = db.query(FeedbackEntry).filter(FeedbackEntry.product_id == product_id).all()
    if not feedback:
        raise HTTPException(status_code=404, detail="No feedback found for this product")
    return feedback

@app.post("/upload-csv/")
def upload_csv_data(db: Session = Depends(get_db)):
    """Load data from feedback.csv file"""
    try:
        # Read CSV
        df = pd.read_csv("feedback.csv")
        
        created_count = 0
        for _, row in df.iterrows():
            # Create product if doesn't exist
            product = db.query(Product).filter(Product.product_id == row['product_id']).first()
            if not product:
                product = Product(product_id=row['product_id'], name=f"Product {row['product_id']}")
                db.add(product)
            
            # Create feedback
            feedback = FeedbackEntry(
                product_id=row['product_id'],
                score=float(row['score']),
                comment=row['comment']
            )
            db.add(feedback)
            created_count += 1
        
        db.commit()
        return {"message": f"Successfully imported {created_count} feedback entries"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

# Run the app
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Customer Feedback API...")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)