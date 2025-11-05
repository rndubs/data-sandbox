#!/bin/bash

# Quick Start Script for Time Series Platform POC

set -e

echo "=========================================="
echo "Time Series Platform - Quick Start"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo ""
echo "Step 1: Building and starting services..."
docker-compose up --build -d

echo ""
echo "Step 2: Waiting for services to be ready..."
sleep 10

# Wait for API to be ready
echo "Waiting for API..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ API failed to start. Check logs with: docker-compose logs api"
    exit 1
fi

echo ""
echo "Step 3: Generating sample data..."
python scripts/generate_sample_data.py

echo ""
echo "Step 4: Verifying setup..."
python scripts/verify_setup.py

echo ""
echo "=========================================="
echo "✓ Platform is ready!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  • Web Client:  http://localhost:3000"
echo "  • API:         http://localhost:8000"
echo "  • API Docs:    http://localhost:8000/docs"
echo "  • MinIO:       http://localhost:9001"
echo ""
echo "Quick Test:"
echo "  python examples/basic_workflow.py"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
