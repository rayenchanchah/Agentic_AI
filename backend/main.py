from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import glob
import json
import uuid
from datetime import datetime
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

# Create storage file if it doesn't exist
KNOWLEDGE_ARTICLES_FILE = "database/knowledge_articles.json"
os.makedirs(os.path.dirname(KNOWLEDGE_ARTICLES_FILE), exist_ok=True)
if not os.path.exists(KNOWLEDGE_ARTICLES_FILE):
    with open(KNOWLEDGE_ARTICLES_FILE, "w") as f:
        json.dump([], f)

# Function to load articles from the Articles folder
def load_articles():
    articles = []
    article_files = glob.glob("Articles/*.txt") + glob.glob("Articles/*.md") + glob.glob("Articles/*.pdf")
    
    for file_path in article_files:
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            article_name = os.path.basename(file_path)
            
            if file_extension in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    articles.append({
                        "name": article_name,
                        "content": content,
                        "source": file_path
                    })
            elif file_extension == '.pdf':
                articles.append({
                    "name": article_name,
                    "content": "PDF content placeholder",
                    "source": file_path
                })
        except Exception as e:
            print(f"Error loading article {file_path}: {str(e)}")
    
    # Also load knowledge articles from JSON file
    try:
        if os.path.exists(KNOWLEDGE_ARTICLES_FILE):
            with open(KNOWLEDGE_ARTICLES_FILE, "r") as f:
                knowledge_articles = json.load(f)
                for article in knowledge_articles:
                    articles.append({
                        "name": article["title"],
                        "content": article["content"],
                        "source": f"Knowledge Base: {article['title']}",
                        "id": article["id"]
                    })
    except Exception as e:
        print(f"Error loading knowledge articles: {str(e)}")
    
    return articles

# Initialize services
articles = load_articles()
ai_analyzer = AIWorkforceAnalyzer()
rag_service = RAGService(articles=articles)  
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
    article_references: List[Dict[str, str]] = []  

class JobEnhancementRequest(BaseModel):
    title: str
    description: Optional[str] = None
    context: Optional[str] = None

class JobEnhancementResponse(BaseModel):
    enhanced_description: str
    web_references: List[dict]
    confidence_score: float
    knowledge_sources: List[str]
    article_references: List[Dict[str, str]] = []  

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
            knowledge_sources=result.knowledge_sources,
            article_references=result.article_references if hasattr(result, 'article_references') else []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                    'knowledge_sources': result.knowledge_sources,
                    'article_references': result.article_references if hasattr(result, 'article_references') else []
                })
            except Exception as e:
                enhanced_jobs.append(job)

        return {"jobs": enhanced_jobs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_database_file(file_path: str) -> List[dict]:
    """Process uploaded database or CSV files"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        jobs = []
        
        if file_ext == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Validate that the CSV has the required columns
            required_columns = ['title', 'description', 'assignedTo']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"Warning: CSV missing required columns: {missing_columns}")
                # Create sample job if CSV format is wrong
                return [create_sample_job("CSV Format Error", 
                       f"The uploaded CSV is missing required columns: {', '.join(missing_columns)}. Please make sure your CSV has these columns: title, description, assignedTo, deadline (optional)")]
            
            # Convert to list of jobs
            for _, row in df.iterrows():
                job = {
                    'title': row['title'],
                    'description': row['description'],
                    'assignedTo': row['assignedTo'],
                    'deadline': row.get('deadline', '2023-12-31'),
                    'sourceDocument': os.path.basename(file_path)
                }
                
                # Add optional fields if they exist
                if 'priority' in row:
                    job['priority'] = row['priority']
                if 'status' in row:
                    job['status'] = row['status']
                if 'tags' in row and not pd.isna(row['tags']):
                    job['tags'] = [tag.strip() for tag in str(row['tags']).split(',')]
                
                jobs.append(job)
                
        elif file_ext in ['.db', '.sqlite', '.sqlite3']:
            import sqlite3
            
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            potential_job_tables = []
            for table in tables:
                table_name = table[0]
                
                # Get column names for this table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [col[1].lower() for col in columns]
                
                # Check if this table has job-like columns
                job_columns = ['title', 'description', 'assigned']
                matches = sum(1 for col in job_columns if any(col in name.lower() for name in column_names))
                
                if matches >= 2:  # Table likely contains job data if it matches at least 2 columns
                    potential_job_tables.append((table_name, column_names))
            
            if not potential_job_tables:
                print(f"Warning: No job tables found in database {file_path}")
                return [create_sample_job("Database Format Error", 
                       "No tables with job data found in the database. Please make sure your database has tables with job-related columns.")]
            
            # Extract data from each potential job table
            for table_name, column_names in potential_job_tables:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100;")
                rows = cursor.fetchall()
                
                # Map column indices to job fields based on column names
                column_mapping = {}
                for i, col in enumerate(column_names):
                    if 'title' in col.lower():
                        column_mapping['title'] = i
                    elif 'desc' in col.lower():
                        column_mapping['description'] = i
                    elif 'assign' in col.lower():
                        column_mapping['assignedTo'] = i
                    elif 'dead' in col.lower() or 'due' in col.lower():
                        column_mapping['deadline'] = i
                    elif 'prior' in col.lower():
                        column_mapping['priority'] = i
                    elif 'status' in col.lower():
                        column_mapping['status'] = i
                    elif 'tag' in col.lower():
                        column_mapping['tags'] = i
                
                if 'title' not in column_mapping or 'description' not in column_mapping:
                    continue  # Skip tables without basic required fields
                
                # Convert rows to jobs
                for row in rows:
                    job = {
                        'title': row[column_mapping['title']],
                        'description': row[column_mapping['description']],
                        'assignedTo': row[column_mapping.get('assignedTo', 0)] if 'assignedTo' in column_mapping else "Unassigned",
                        'deadline': row[column_mapping.get('deadline', 0)] if 'deadline' in column_mapping else "2023-12-31",
                        'sourceDocument': os.path.basename(file_path)
                    }
                    
                    if 'priority' in column_mapping:
                        job['priority'] = row[column_mapping['priority']]
                    if 'status' in column_mapping:
                        job['status'] = row[column_mapping['status']]
                    if 'tags' in column_mapping and row[column_mapping['tags']]:
                        job['tags'] = [tag.strip() for tag in str(row[column_mapping['tags']]).split(',')]
                    
                    jobs.append(job)
            
            conn.close()
            
        # If no jobs were extracted, return a sample job
        if not jobs:
            jobs = [create_sample_job("No Jobs Found", 
                   "Could not extract any jobs from the uploaded file. Please check the file format.")]
        
        return jobs
    except Exception as e:
        print(f"Error processing database file: {str(e)}")
        return [create_sample_job("Processing Error", 
               f"An error occurred while processing the file: {str(e)}")]

async def process_document_file(file_path: str) -> List[dict]:
    """Process uploaded PDF or HTML files"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            try:
                import fitz  # PyMuPDF
                
                text_content = ""
                job_candidates = []
                
                # Extract text from PDF
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text_content += page.get_text()
                
                # Look for job-like sections in the text
                lines = text_content.split('\n')
                current_job = None
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this line looks like a job title (short line with capitalized words)
                    if len(line) < 100 and any(word[0].isupper() for word in line.split() if word):
                        # If we were building a job, save it
                        if current_job and 'description' in current_job:
                            job_candidates.append(current_job)
                        
                        # Start a new job
                        current_job = {
                            'title': line,
                            'sourceDocument': os.path.basename(file_path)
                        }
                    elif current_job and 'description' not in current_job:
                        # Add the first non-title line as description
                        current_job['description'] = line
                        
                        # Look for assignee information in nearby lines
                        for j in range(i+1, min(i+10, len(lines))):
                            if 'assign' in lines[j].lower() or 'responsible' in lines[j].lower():
                                assignee_line = lines[j].strip()
                                parts = assignee_line.split(':')
                                if len(parts) > 1:
                                    current_job['assignedTo'] = parts[1].strip()
                                    break
                        
                        # If no assignee found, use a default
                        if 'assignedTo' not in current_job:
                            current_job['assignedTo'] = "Unassigned"
                        
                        # Look for deadline information
                        for j in range(i+1, min(i+10, len(lines))):
                            if any(term in lines[j].lower() for term in ['deadline', 'due date', 'due by']):
                                deadline_line = lines[j].strip()
                                current_job['deadline'] = deadline_line.split(':')[-1].strip()
                                break
                        
                        # If no deadline found, use a default
                        if 'deadline' not in current_job:
                            current_job['deadline'] = "2023-12-31"
                    
                # Save the last job if we were building one
                if current_job and 'description' in current_job:
                    job_candidates.append(current_job)
                
                # Clean up jobs (ensure they have all required fields and reasonable content)
                jobs = []
                for job in job_candidates:
                    if len(job['title']) > 5 and len(job['description']) > 10:
                        jobs.append(job)
                
                if not jobs:
                    # If we couldn't extract structured jobs, create a sample with the first 1000 chars of content
                    preview = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                    jobs = [create_sample_job(
                        "PDF Content", 
                        f"Content extracted from PDF: {preview}",
                        os.path.basename(file_path)
                    )]
            except ImportError:
                # Fallback if PyMuPDF is not installed
                return [create_sample_job(
                    "PDF Processing", 
                    "The PDF processing module is not installed. Please install PyMuPDF (fitz) to process PDFs.",
                    os.path.basename(file_path)
                )]
                
        elif file_ext == '.html':
            try:
                from bs4 import BeautifulSoup
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Try to extract jobs from HTML
                jobs = []
                
                # Look for job listings in common container elements
                job_containers = soup.select('div.job, article, section, .card, .listing')
                
                if not job_containers:
                    # If no specific containers found, try headers as job titles
                    headers = soup.select('h1, h2, h3')
                    
                    for header in headers:
                        title = header.get_text().strip()
                        if 5 < len(title) < 100:  # Reasonable title length
                            # Look for description in the next sibling paragraph
                            desc_elem = header.find_next('p')
                            description = desc_elem.get_text().strip() if desc_elem else ""
                            
                            if len(description) > 10:
                                jobs.append({
                                    'title': title,
                                    'description': description,
                                    'assignedTo': "Unassigned",
                                    'deadline': "2023-12-31",
                                    'sourceDocument': os.path.basename(file_path)
                                })
                else:
                    # Process job containers
                    for container in job_containers:
                        # Try to find title
                        title_elem = container.select_one('h1, h2, h3, h4, .title, .job-title')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Try to find description
                        desc_elem = container.select_one('p, .description, .job-description')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        # Try to find assignee
                        assignee_elem = container.select_one('.assignee, .assigned-to')
                        assignee = assignee_elem.get_text().strip() if assignee_elem else "Unassigned"
                        
                        # Try to find deadline
                        deadline_elem = container.select_one('.deadline, .due-date')
                        deadline = deadline_elem.get_text().strip() if deadline_elem else "2023-12-31"
                        
                        jobs.append({
                            'title': title,
                            'description': description,
                            'assignedTo': assignee,
                            'deadline': deadline,
                            'sourceDocument': os.path.basename(file_path)
                        })
                
                if not jobs:
                    # If extraction failed, create a sample job with page title
                    title = soup.title.string if soup.title else "HTML Document"
                    jobs = [create_sample_job(
                        title, 
                        f"Content from HTML document: {soup.get_text()[:500]}...",
                        os.path.basename(file_path)
                    )]
            except ImportError:
                # Fallback if BeautifulSoup is not installed
                return [create_sample_job(
                    "HTML Processing", 
                    "The HTML processing module is not installed. Please install Beautiful Soup to process HTML files.",
                    os.path.basename(file_path)
                )]
                
        elif file_ext == '.txt':
            # Process text file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            
            # Simple parsing for job-like content
            jobs = []
            
            # Split into potential sections
            sections = text_content.split('\n\n')
            current_title = os.path.basename(file_path)
            description_parts = []
            
            # Look for job-like patterns
            for section in sections:
                if not section.strip():
                    continue
                
                lines = section.strip().split('\n')
                
                # If section starts with a short line (potential title)
                if len(lines) > 1 and len(lines[0]) < 100 and any(word[0].isupper() for word in lines[0].split() if word):
                    # If we collected description for a previous title, create a job
                    if description_parts and len(description_parts) > 0:
                        jobs.append({
                            'title': current_title,
                            'description': '\n'.join(description_parts),
                            'assignedTo': "Unassigned",
                            'deadline': "2023-12-31",
                            'sourceDocument': os.path.basename(file_path)
                        })
                    
                    # Start a new job
                    current_title = lines[0]
                    description_parts = lines[1:]
                else:
                    # Continue adding to description
                    description_parts.extend(lines)
            
            # Add the last job if we have one
            if description_parts:
                jobs.append({
                    'title': current_title,
                    'description': '\n'.join(description_parts),
                    'assignedTo': "Unassigned",
                    'deadline': "2023-12-31",
                    'sourceDocument': os.path.basename(file_path)
                })
            
            # If no structured jobs found, create a sample with the text content
            if not jobs:
                preview = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                jobs = [create_sample_job(
                    "Text Content", 
                    f"Content extracted from text file: {preview}",
                    os.path.basename(file_path)
                )]
            
            return jobs
        
        return jobs
    except Exception as e:
        print(f"Error processing document file: {str(e)}")
        return [create_sample_job("Processing Error", 
               f"An error occurred while processing the file: {str(e)}")]

def create_sample_job(title, description, source_document=None):
    """Create a sample job with the given title and description"""
    return {
        'title': title,
        'description': description,
        'assignedTo': "AI System",
        'deadline': "2023-12-31",
        'sourceDocument': source_document,
        'aiEnhanced': True
    }

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
        all_article_references = []
        
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
                "confidence_score": enhanced_info.confidence_score,
                "article_references": enhanced_info.article_references
            })
            
            # Collect all article references
            if enhanced_info.article_references:
                all_article_references.extend(enhanced_info.article_references)

        # Update request with enhanced information
        enhanced_request = TeamAnalysisRequest(
            **request.dict(),
            members=enhanced_members
        )

        # Perform analysis with enhanced information
        analysis_result = await ai_analyzer.analyze_team(enhanced_request)
        
        # Add article references to the analysis result
        if not hasattr(analysis_result, 'article_references'):
            analysis_result.article_references = []
        
        # Add unique article references
        seen_refs = set()
        for ref in all_article_references:
            ref_key = f"{ref.get('name', '')}-{ref.get('source', '')}"
            if ref_key not in seen_refs:
                analysis_result.article_references.append(ref)
                seen_refs.add(ref_key)
                
        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/articles")
async def get_articles():
    """
    Get a list of all available articles
    """
    return {"articles": [{"name": article["name"], "source": article["source"]} for article in articles]}

# Knowledge Article Model
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

# API endpoints for Knowledge Articles
@app.get("/api/knowledge-articles", response_model=List[KnowledgeArticleResponse])
async def get_knowledge_articles():
    try:
        with open(KNOWLEDGE_ARTICLES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading knowledge articles: {str(e)}")
        return []

@app.post("/api/knowledge-articles", response_model=KnowledgeArticleResponse)
async def create_knowledge_article(article: KnowledgeArticleCreate):
    try:
        global articles, rag_service
        
        with open(KNOWLEDGE_ARTICLES_FILE, "r") as f:
            articles_data = json.load(f)
        
        new_article = {
            **article.dict(),
            "id": str(uuid.uuid4()),
            "dateAdded": datetime.now().isoformat(),
            "usageCount": 0
        }
        
        articles_data.append(new_article)
        
        with open(KNOWLEDGE_ARTICLES_FILE, "w") as f:
            json.dump(articles_data, f, indent=2)
        
        # Refresh RAG service with new knowledge
        articles = load_articles()
        rag_service = RAGService(articles=articles)
        
        return new_article
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating article: {str(e)}")

@app.delete("/api/knowledge-articles/{article_id}")
async def delete_knowledge_article(article_id: str):
    try:
        global articles, rag_service
        
        with open(KNOWLEDGE_ARTICLES_FILE, "r") as f:
            articles_data = json.load(f)
        
        articles_data = [a for a in articles_data if a["id"] != article_id]
        
        with open(KNOWLEDGE_ARTICLES_FILE, "w") as f:
            json.dump(articles_data, f, indent=2)
        
        # Refresh RAG service with updated knowledge
        articles = load_articles()
        rag_service = RAGService(articles=articles)
        
        return {"status": "success", "message": f"Article {article_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting article: {str(e)}")

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)