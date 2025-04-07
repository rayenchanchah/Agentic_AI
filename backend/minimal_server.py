from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Configure CORS - IMPORTANT!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample job data
SAMPLE_JOBS = [
    {
        "title": "Analyze Customer Data",
        "description": "Review and analyze customer usage patterns to identify trends",
        "assignedTo": "Data Analyst",
        "deadline": "2023-12-01",
        "aiEnhanced": True,
        "references": ["Customer Database", "Previous Reports"],
        "webReferences": [
            {"url": "https://example.com/analytics", "title": "Analytics Best Practices", "relevance": 95}
        ]
    },
    {
        "title": "Update Website Content",
        "description": "Refresh product descriptions and imagery on the main website",
        "assignedTo": "Content Manager",
        "deadline": "2023-11-15",
        "aiEnhanced": True,
        "references": ["Brand Guidelines"],
        "webReferences": [
            {"url": "https://example.com/content", "title": "Content Strategy Guide", "relevance": 90}
        ]
    }
]

@app.get("/")
def root():
    return {"message": "Minimal File Upload Server"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Don't actually process the file, just return sample data
    print(f"Received file: {file.filename}")
    return {"jobs": SAMPLE_JOBS}

@app.get("/api/knowledge-articles")
def get_articles():
    return []

if __name__ == "__main__":
    print("Starting minimal server on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)