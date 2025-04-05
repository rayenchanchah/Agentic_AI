from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KnowledgeArticle(BaseModel):
    id: str
    title: str
    content: str
    source: Optional[str] = None
    author: Optional[str] = None
    dateAdded: str
    tags: Optional[List[str]] = None
    usageCount: int = 0

# Sample data
sample_jobs = [
    {
        "title": "Develop Frontend Interface",
        "description": "Create responsive UI components for the dashboard",
        "assignedTo": "John Smith",
        "deadline": "2023-12-15",
        "aiEnhanced": True,
        "references": ["Angular Documentation", "Material Design Guidelines"],
        "webReferences": [
            {"url": "https://angular.io", "title": "Angular Documentation", "relevance": 95},
            {"url": "https://material.io", "title": "Material Design", "relevance": 85}
        ]
    },
    {
        "title": "Implement API Integration",
        "description": "Connect frontend with backend services",
        "assignedTo": "Jane Doe",
        "deadline": "2024-01-10",
        "aiEnhanced": True,
        "references": ["REST API Best Practices"],
        "webReferences": [
            {"url": "https://restfulapi.net", "title": "RESTful API Guidelines", "relevance": 90}
        ]
    }
]

sample_articles = [
    {
        "id": "1",
        "title": "AI in Modern Workplaces",
        "content": "Artificial intelligence is transforming how teams collaborate and complete tasks...",
        "dateAdded": "2023-11-10T12:00:00Z",
        "source": "Harvard Business Review",
        "author": "Dr. AI Researcher",
        "tags": ["AI", "productivity", "teamwork"],
        "usageCount": 12
    }
]

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Just read the first few bytes to verify the file exists
        content = await file.read(1024)
        await file.seek(0)  # Reset file pointer
        
        # Simply return sample jobs without any actual processing
        return {"jobs": sample_jobs}
    except Exception as e:
        print(f"Error in file upload: {str(e)}")
        # Return sample jobs even if there's an error
        return {"jobs": sample_jobs}

@app.get("/api/knowledge-articles")
async def get_articles():
    return sample_articles

@app.post("/api/knowledge-articles")
async def add_article(article: KnowledgeArticle):
    # In a real app, you'd save this to a database
    new_article = {
        "id": "2",
        "title": article.title,
        "content": article.content,
        "dateAdded": "2023-12-05T10:30:00Z",
        "source": article.source,
        "author": article.author,
        "tags": article.tags or [],
        "usageCount": 0
    }
    
    sample_articles.append(new_article)
    return new_article

@app.delete("/api/knowledge-articles/{article_id}")
async def delete_article(article_id: str):
    # Just return success, since it's just a test
    return {"status": "success", "message": f"Article {article_id} deleted"}

if __name__ == "__main__":
    print("Starting test server on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000) 