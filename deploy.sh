#!/bin/bash

# Deploy backend
echo "Deploying backend..."
cd backend
railway up

# Deploy frontend
echo "Deploying frontend..."
cd ../frontend
vercel --prod