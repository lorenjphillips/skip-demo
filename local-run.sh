#!/bin/bash

# Start Backend Server
echo "Deploying backend..."
cd backend
python main.py

# Deploy frontend
echo "Deploying frontend..."
cd ../frontend
npm run dev