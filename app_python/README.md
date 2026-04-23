# DevOps Info Service (Python / FastAPI)

[![Python CI/CD](https://github.com/flowelx/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/flowelx/DevOps-Core-Course/actions/workflows/python-ci.yml)

## Overview

This FastAPI application delivers runtime and system data through HTTP endpoints. Built as a modular platform for DevOps education, it enables practical exploration of containerization, CI/CD pipelines, monitoring solutions, and infrastructure automation concepts.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Docker 25.0.0+ (for containerized deployment)
- Docker Compose (for volume management)

## Installation

1. Clone the repository and navigate to the project directory:

```bash
cd app_python
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration

The application runs on `0.0.0.0:5000` with debug mode disabled by default:

```bash
python app.py
```

### Custom Configuration with Environment Variables

You can customize the server behavior using environment variables:

```bash
# Run on localhost:8080
PORT=8080 python app.py

# Run on 127.0.0.1:3000 with debug/reload enabled
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py

# Specify custom visits file location
VISITS_FILE=./custom_visits.json python app.py
```

### Testing the Endpoints

After starting the application, test the endpoints using curl:

```bash
# Home endpoint
curl http://localhost:8080/

# Check current visit count
curl http://localhost:8000/visits

# Health check
curl http://localhost:8080/health
```

## API Endpoints

### GET `/`

Returns comprehensive JSON metadata with the following top-level sections:

- **service** – name, version, description, framework
- **system** – hostname, platform, platform_version, architecture, cpu_count, python_version
- **runtime** – uptime_seconds, uptime_human, current_time, timezone
- **request** – client_ip, user_agent, method, path
- **endpoints** – list of available paths and their purpose

### GET `/visits`

Returns the current visit count without incrementing:

```json
{
  "visits": 42,
  "last_updated": "2026-04-16T10:30:00Z"
}
```

### GET `/health`

Returns a compact health status document:

- **status** – string status ("healthy")
- **timestamp** – current UTC timestamp
- **uptime_seconds** – number of seconds the process has been running

### GET `/metrics`

Exports Prometheus metrics including:

- HTTP request counts by method and endpoint
- Request duration histograms
- Active requests gauge
- External API call counters

### GET `/error`

Test endpoint that returns a 500 error for testing error handling and monitoring.

## Configuration

The application is configured via environment variables. All variables are optional; if not set, the defaults below are used.

| Variable | Default   | Description                                  |
|----------|-----------|----------------------------------------------|
| `HOST`   | `0.0.0.0` | IP address the server binds to               |
| `PORT`   | `5000`    | TCP port the application listens on          |
| `DEBUG`  | `False`   | When `true`, enables debug mode with auto-reload and detailed error messages |
| `VISIT_FILE` | `/data/visits.json` | Path to the persistent visit counter file |

--- 
---

# Docker Containerization

## Prerequisites

- Docker 25.0.0+
- Docker Compose (for volume management)

## Building the Image Locally

To build the Docker image:

```bash
cd app_python
docker build -t [image-name]:[tag] -f Dockerfile .
```

**Example:**

```bash
docker build -t my-fastapi-app:latest -f Dockerfile .
```

Running with Docker Compose

The application uses Docker volumes to persist visit counter data across container restarts:

```bash
# Start the application with volume mount
docker compose up -d

# View logs
docker compose logs -f app

# Stop the application
docker compose down

# Data persists! Restart and check visits
docker compose up -d
curl http://localhost:8000/visits
```

## Running a Standalone Container

To run application in a container:

```bash
docker run -d -p [host-port]:[container-port] --name [container-name] [image-name]:[tag]
```

**Example:**

```bash
docker run -d -p 5000:5000 --name myapp my-fastapi-app:latest
```

## Environment Variables in Docker

When running in Docker, you can override these environment variables:

```bash
docker run -d -p 5000:5000 \
  -e HOST=0.0.0.0 \
  -e PORT=5000 \
  -e DEBUG=False \
  -e VISITS_FILE=/data/visits.json \
  --name myapp \
  my-fastapi-app:1.0.0
```

## Pulling from Docker Hub

To use the pre-built image from Docker Hub registry:

```bash
# Pull latest version
docker pull flowelx/fastapi-lab-app:latest

# Run pulled image
docker run -d -p 5000:5000 flowelx/fastapi-lab-app:latest
```
