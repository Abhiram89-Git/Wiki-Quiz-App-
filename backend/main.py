from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List

# Import utility functions
from scraper import scrape_wikipedia
from quiz_generator import generate_quiz_with_llm

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/wiki_quiz_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class QuizRecord(Base):
    __tablename__ = "quiz_records"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    summary = Column(Text)
    key_entities = Column(JSON)
    sections = Column(JSON)
    quiz = Column(JSON)
    related_topics = Column(JSON)
    raw_html = Column(Text, nullable=True)  # Bonus: Store raw HTML
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# API Models
class QuizGenerationRequest(BaseModel):
    url: str

class QuizResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: str
    key_entities: dict
    sections: list
    quiz: list
    related_topics: list
    created_at: datetime

class HistoryItem(BaseModel):
    id: int
    url: str
    title: str
    created_at: datetime

# FastAPI App
app = FastAPI(
    title="Wikipedia Quiz Generator API",
    description="Generate quizzes from Wikipedia articles using LLM",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Wikipedia Quiz Generator API", "version": "1.0.0"}

@app.post("/api/generate-quiz", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerationRequest, db: Session = None):
    """
    Generate a quiz from a Wikipedia article URL.
    Scrapes content, processes with LLM, and stores in database.
    """
    db = next(get_db()) if db is None else db
    
    try:
        # Validate URL
        if not request.url.startswith("https://en.wikipedia.org/wiki/"):
            raise HTTPException(status_code=400, detail="Invalid Wikipedia URL")
        
        # Check if already processed (Bonus: Caching)
        existing = db.query(QuizRecord).filter(QuizRecord.url == request.url).first()
        if existing:
            logger.info(f"Cache hit for URL: {request.url}")
            return QuizResponse(**existing.__dict__)
        
        logger.info(f"Starting quiz generation for: {request.url}")
        
        # Step 1: Scrape Wikipedia
        scraped_data = scrape_wikipedia(request.url)
        
        # Step 2: Generate quiz with LLM
        quiz_data = generate_quiz_with_llm(
            content=scraped_data["content"],
            title=scraped_data["title"],
            sections=scraped_data["sections"]
        )
        
        # Step 3: Store in database
        db_record = QuizRecord(
            url=request.url,
            title=scraped_data["title"],
            summary=scraped_data["summary"],
            key_entities=scraped_data["key_entities"],
            sections=scraped_data["sections"],
            quiz=quiz_data["quiz"],
            related_topics=quiz_data["related_topics"],
            raw_html=scraped_data.get("raw_html")  # Bonus: Store HTML
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Successfully generated quiz for: {request.url}")
        return QuizResponse(**db_record.__dict__)
    
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history", response_model=List[HistoryItem])
def get_quiz_history(db: Session = None):
    """
    Retrieve list of all previously processed Wikipedia articles.
    """
    db = next(get_db()) if db is None else db
    
    try:
        records = db.query(QuizRecord).order_by(QuizRecord.created_at.desc()).all()
        return [HistoryItem(**record.__dict__) for record in records]
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/{quiz_id}", response_model=QuizResponse)
def get_quiz_details(quiz_id: int, db: Session = None):
    """
    Get full details of a specific quiz.
    """
    db = next(get_db()) if db is None else db
    
    try:
        record = db.query(QuizRecord).filter(QuizRecord.id == quiz_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return QuizResponse(**record.__dict__)
    except Exception as e:
        logger.error(f"Error fetching quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/validate-url")
def validate_url(url: str):
    """
    Bonus: Validate and preview Wikipedia article before full processing.
    """
    try:
        if not url.startswith("https://en.wikipedia.org/wiki/"):
            return {"valid": False, "message": "Invalid Wikipedia URL"}
        
        title = scrape_wikipedia(url, preview=True)["title"]
        return {"valid": True, "title": title}
    except Exception as e:
        return {"valid": False, "message": str(e)}

@app.delete("/api/quiz/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = None):
    """
    Delete a quiz record from history.
    """
    db = next(get_db()) if db is None else db
    
    try:
        record = db.query(QuizRecord).filter(QuizRecord.id == quiz_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        db.delete(record)
        db.commit()
        return {"message": "Quiz deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting quiz: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)