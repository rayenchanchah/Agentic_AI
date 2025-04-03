# AI Workforce Impact Analyzer

An AI-powered system for analyzing the impact of generative AI on workforce sustainability.

## Features

- Automated research and analysis of AI impact on various professions
- Team-based impact assessment
- Detailed reporting and recommendations
- Workforce sustainability strategies
- Practical implementation guidance

## Tech Stack

- **Frontend**: Angular
- **Backend**: Python with FastAPI
- **AI/ML**: LangChain, OpenAI GPT
- **Database**: PostgreSQL

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```
3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key and other required credentials
4. Run the application:
   ```bash
   # Backend
   cd backend
   uvicorn main:app --reload
   
   # Frontend
   cd frontend
   ng serve
   ```

## API Documentation

The API documentation will be available at `http://localhost:8000/docs` when running the backend server.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.
