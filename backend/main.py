from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from ai_agent.analyzer import AIWorkforceAnalyzer
from database.models import Base, engine
from database.database import get_db
from sqlalchemy.orm import Session
from services.rag_service import RAGService
from services.web_search import WebSearchService

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Workforce Impact Analyzer",
    description="API for analyzing the impact of generative AI on workforce sustainability",
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

# Initialize services
ai_analyzer = AIWorkforceAnalyzer()
rag_service = RAGService()
web_search_service = WebSearchService()

class TeamMember(BaseModel):
    role: str
    responsibilities: List[str]
    experience_level: str
    department: str

class TeamAnalysisRequest(BaseModel):
    team_name: str
    members: List[TeamMember]
    industry: str
    company_size: str
    current_ai_usage: Optional[str] = None

class AnalysisResponse(BaseModel):
    team_name: str
    impact_summary: dict
    recommendations: List[str]
    risk_assessment: dict
    upskilling_opportunities: List[str]

class JobEnhancementRequest(BaseModel):
    title: str
    description: Optional[str] = None
    context: Optional[str] = None

class JobEnhancementResponse(BaseModel):
    enhanced_description: str
    web_references: List[dict]
    confidence_score: float
    knowledge_sources: List[str]

@app.post("/api/enhance-job", response_model=JobEnhancementResponse)
async def enhance_job(request: JobEnhancementRequest):
    try:
        # Get enhanced information using RAG
        result = await rag_service.retrieve_relevant_info(
            request.title,
            request.context
        )
        
        return JobEnhancementResponse(
            enhanced_description=result.enhanced_description,
            web_references=result.web_references,
            confidence_score=result.confidence_score,
            knowledge_sources=result.knowledge_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ['.csv', '.db', '.sqlite', '.sqlite3', '.pdf', '.html']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )

        # Save file temporarily
        file_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process file based on type
        jobs = []
        if file_ext in ['.csv', '.db', '.sqlite', '.sqlite3']:
            jobs = await process_database_file(file_path)
        elif file_ext in ['.pdf', '.html']:
            jobs = await process_document_file(file_path)

        os.remove(file_path)

        # Enhance each job with RAG
        enhanced_jobs = []
        for job in jobs:
            try:
                result = await rag_service.retrieve_relevant_info(
                    job['title'],
                    job.get('description')
                )
                enhanced_jobs.append({
                    **job,
                    'enhanced_description': result.enhanced_description,
                    'web_references': result.web_references,
                    'confidence_score': result.confidence_score,
                    'knowledge_sources': result.knowledge_sources
                })
            except Exception as e:
                enhanced_jobs.append(job)

        return {"jobs": enhanced_jobs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_database_file(file_path: str) -> List[dict]:
    # Implementation depends on your database/CSV structure
    return []

async def process_document_file(file_path: str) -> List[dict]:
    # Implementation depends on your document structure
    # This is a placeholder
    return []

@app.post("/api/analyze-team", response_model=AnalysisResponse)
async def analyze_team(
    request: TeamAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze the impact of AI on a team and generate recommendations
    """
    try:
        # Enhance each team member's role with RAG
        enhanced_members = []
        for member in request.members:
            enhanced_info = await enhance_job(
                JobEnhancementRequest(
                    title=member.role,
                    description=" ".join(member.responsibilities),
                    context=f"Industry: {request.industry}, Company Size: {request.company_size}"
                )
            )
            
            enhanced_members.append({
                **member.dict(),
                "enhanced_description": enhanced_info.enhanced_description,
                "web_references": enhanced_info.web_references,
                "confidence_score": enhanced_info.confidence_score
            })

        # Update request with enhanced information
        enhanced_request = TeamAnalysisRequest(
            **request.dict(),
            members=enhanced_members
        )

        # Perform analysis with enhanced information
        analysis_result = await ai_analyzer.analyze_team(enhanced_request)
        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 