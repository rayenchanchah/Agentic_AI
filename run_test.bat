@echo off
echo Starting the AI-Powered Team Jobs Manager (Test Version)...
echo.

echo Starting test backend server...
start cmd /k "cd backend && python test_simple_server.py"

echo Starting frontend server...
start cmd /k "cd frontend && ng serve --open"

echo.
echo The application should open in your browser shortly.
echo Test backend API is running at http://localhost:3000
echo Frontend is running at http://localhost:4200
echo.
echo Press any key to exit this window...
pause > nul 