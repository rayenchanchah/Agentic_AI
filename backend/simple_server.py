from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
from datetime import datetime
import uuid

app = FastAPI(
    title="Simple Team Jobs Manager",
    description="Simplified API for Team Jobs Manager file uploads",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database
knowledge_articles = []
uploaded_jobs = []

class KnowledgeArticleCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

class KnowledgeArticleResponse(KnowledgeArticleCreate):
    id: str
    dateAdded: str
    usageCount: int = 0

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ['.csv', '.db', '.sqlite', '.sqlite3', '.pdf', '.html', '.txt']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )

        # Create sample jobs based on file name
        jobs = [
            {
                'title': f"Job from {file.filename}",
                'description': f"This is a sample job extracted from {file.filename}",
                'assignedTo': "AI System",
                'deadline': "2023-12-31",
                'sourceDocument': file.filename,
                'aiEnhanced': True,
                'references': ["Reference 1", "Reference 2"],
                'webReferences': [
                    {"url": "https://example.com/1", "title": "Example Resource 1", "relevance": 95},
                    {"url": "https://example.com/2", "title": "Example Resource 2", "relevance": 85}
                ]
            },
            {
                'title': f"Another job from {file.filename}",
                'description': f"This is another sample job extracted from {file.filename}",
                'assignedTo': "Team Lead",
                'deadline': "2023-11-15",
                'sourceDocument': file.filename,
                'aiEnhanced': True,
                'references': ["Reference 3"],
                'webReferences': [
                    {"url": "https://example.com/3", "title": "Example Resource 3", "relevance": 90}
                ]
            }
        ]
        
        # Store jobs in memory
        uploaded_jobs.extend(jobs)
        
        return {"jobs": jobs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-articles", response_model=List[KnowledgeArticleResponse])
async def get_knowledge_articles():
    return knowledge_articles

@app.post("/api/knowledge-articles", response_model=KnowledgeArticleResponse)
async def create_knowledge_article(article: KnowledgeArticleCreate):
    try:
        new_article = {
            **article.dict(),
            "id": str(uuid.uuid4()),
            "dateAdded": datetime.now().isoformat(),
            "usageCount": 0
        }
        
        knowledge_articles.append(new_article)
        return new_article
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating article: {str(e)}")

@app.delete("/api/knowledge-articles/{article_id}")
async def delete_knowledge_article(article_id: str):
    try:
        global knowledge_articles
        knowledge_articles = [a for a in knowledge_articles if a["id"] != article_id]
        return {"status": "success", "message": f"Article {article_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting article: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 