#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Skip Demo Local Development Setup ===${NC}"

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Cleaning up background processes...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}Step 1: Setting up backend environment${NC}"

# Navigate to backend
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Warning: No .env file found in backend directory${NC}"
    echo -e "${YELLOW}Please create a .env file with your OPENAI_API_KEY${NC}"
fi

# Check if local database exists and initialize if needed
echo -e "${BLUE}Step 2: Checking local database${NC}"
if [ ! -d "chroma_db" ] || [ -z "$(ls -A chroma_db 2>/dev/null)" ]; then
    echo -e "${YELLOW}Local database not found or empty. Running ingestion...${NC}"
    python3 ingest.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database ingestion completed successfully${NC}"
    else
        echo -e "${RED}Database ingestion failed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Local database found${NC}"
    python3 -c "import chromadb; c=chromadb.PersistentClient(path='./chroma_db'); print(f'Documents in database: {c.get_collection(\"podcast_transcripts\").count()}')"
fi

# Check backend port
if check_port 8000; then
    echo -e "${YELLOW}Port 8000 is already in use. Attempting to free it...${NC}"
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    sleep 2
fi

echo -e "${BLUE}Step 3: Starting backend server${NC}"
echo -e "${GREEN}Backend will be available at: http://localhost:8000${NC}"
echo -e "${GREEN}API docs will be available at: http://localhost:8000/docs${NC}"

# Start backend in background
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 3

# Test backend health
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is healthy and responding${NC}"
        break
    else
        if [ $i -eq 10 ]; then
            echo -e "${RED}Backend failed to start properly${NC}"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
        echo -e "${YELLOW}Waiting for backend... (attempt $i/10)${NC}"
        sleep 2
    fi
done

# Navigate to frontend
cd ../frontend

echo -e "${BLUE}Step 4: Setting up frontend${NC}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

# Check frontend port
if check_port 3000; then
    echo -e "${YELLOW}Port 3000 is already in use. Attempting to free it...${NC}"
    lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
    sleep 2
fi

echo -e "${BLUE}Step 5: Starting frontend development server${NC}"
echo -e "${GREEN}Frontend will be available at: http://localhost:3000${NC}"

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo -e "${YELLOW}Waiting for frontend to start...${NC}"
sleep 5

# Test frontend
for i in {1..10}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend is running and responding${NC}"
        break
    else
        if [ $i -eq 10 ]; then
            echo -e "${YELLOW}Frontend may still be starting up...${NC}"
        fi
        echo -e "${YELLOW}Waiting for frontend... (attempt $i/10)${NC}"
        sleep 2
    fi
done

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "${GREEN}✓ Backend: http://localhost:8000${NC}"
echo -e "${GREEN}✓ Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}✓ API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both servers${NC}"

# Wait for user interruption
while true; do
    sleep 1
done