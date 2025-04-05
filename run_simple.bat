@echo off
echo Starting the AI-Powered Team Jobs Manager (Simple Version)...
echo.

echo Starting simple backend server...
start cmd /k "cd backend && python -m uvicorn simple_server:app --reload --port 3000"

echo Starting frontend server...
start cmd /k "cd frontend && ng serve --open"

echo.
echo The application should open in your browser shortly.
echo Simple backend API is running at http://localhost:3000
echo Frontend is running at http://localhost:4200
echo.
echo Press any key to exit this window...
pause > nul 