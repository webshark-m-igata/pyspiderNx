#!/bin/bash

# Set OPENSSL_CONF to /dev/null to avoid OpenSSL configuration errors
export OPENSSL_CONF=/dev/null

# Set Python optimization flags (but not too aggressive to avoid compatibility issues)
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Set memory limits
export NODE_OPTIONS="--max-old-space-size=2048"

# Configuration file
CONFIG_FILE="config.json"

# Create necessary directories
mkdir -p data
mkdir -p logs
mkdir -p puppeteer_cache

# Function to extract port from config.json
extract_port() {
    local component=$1
    local port_key=$2
    local port=$(grep -A 10 "\"$component\"" $CONFIG_FILE | grep "\"$port_key\"" | sed -E 's/.*: *([0-9]+).*/\1/')
    echo $port
}

# Extract ports from config.json
PHANTOMJS_PORT=$(extract_port "phantomjs" "port")
PUPPETEER_PORT=$(extract_port "puppeteer" "port")
WEBUI_PORT=$(extract_port "webui" "port")
SCHEDULER_PORT=$(extract_port "scheduler" "xmlrpc_port")
FETCHER_PORT=$(extract_port "fetcher" "xmlrpc_port")

echo "Extracted ports from $CONFIG_FILE:"
echo "  - PhantomJS port: $PHANTOMJS_PORT"
echo "  - Puppeteer port: $PUPPETEER_PORT"
echo "  - WebUI port: $WEBUI_PORT"
echo "  - Scheduler port: $SCHEDULER_PORT"
echo "  - Fetcher port: $FETCHER_PORT"

# Kill processes using these ports
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill -9 $pid
    else
        echo "No process found using port $port"
    fi
}

echo "Killing processes using pyspider ports..."
kill_port $PHANTOMJS_PORT
kill_port $PUPPETEER_PORT
kill_port $WEBUI_PORT
kill_port $SCHEDULER_PORT
kill_port $FETCHER_PORT

# Kill any remaining phantomjs or puppeteer processes
echo "Killing any remaining phantomjs or puppeteer processes..."
pkill -f "phantomjs.*phantomjs_fetcher.js" || true
pkill -f "node.*puppeteer_fetcher.js" || true
pkill -f "phantomjs" || true
pkill -f "node.*puppeteer" || true

# Kill any processes using the ports
echo "Killing processes using ports..."
for port in $(grep -o '"port": [0-9]\+' $CONFIG_FILE | grep -o '[0-9]\+'); do
    pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill -9 $pid
    fi
done

# Kill any node processes using puppeteer_fetcher.js
for pid in $(ps aux | grep "node.*puppeteer_fetcher.js" | grep -v grep | awk '{print $2}'); do
    echo "Killing node process $pid"
    kill -9 $pid
done

# Kill any phantomjs processes
for pid in $(ps aux | grep "phantomjs" | grep -v grep | awk '{print $2}'); do
    echo "Killing phantomjs process $pid"
    kill -9 $pid
done

# Wait a moment for processes to terminate
sleep 2

# Clean up temporary files
echo "Cleaning up temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Optimize SQLite database if it exists and sqlite3 command is available
if [ -f "data/pyspider.db" ] && command -v sqlite3 &> /dev/null; then
    echo "Optimizing SQLite database..."
    sqlite3 data/pyspider.db "VACUUM; ANALYZE;"
fi

# Performance tuning for Python
echo "Setting up performance optimizations..."

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random

# Run pyspider with config.json
echo "Starting pyspider with optimized settings..."
python -O run.py -c $CONFIG_FILE "$@" 2>&1 | tee -a logs/pyspider_$(date +%Y%m%d).log
