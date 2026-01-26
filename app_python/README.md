# DevOps Info Service (Python / FastAPI)

## Overview

This FastAPI application delivers runtime and system data through HTTP endpoints. Built as a modular platform for DevOps education, it enables practical exploration of containerization, CI/CD pipelines, monitoring solutions, and infrastructure automation concepts.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git (for cloning the repository)
- Optional: curl or HTTP client for testing endpoints

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

The application runs on `0.0.0.0:8080` with debug mode disabled by default:

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
```

### Testing the Endpoints

After starting the application, test the endpoints using curl:

```bash
curl http://localhost:8080/
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

### GET `/health`

Returns a compact health status document:

- **status** – string status ("healthy")
- **timestamp** – current UTC timestamp in ISO 8601 format
- **uptime_seconds** – number of seconds the process has been running

## Configuration

The application is configured via environment variables. All variables are optional; if not set, the defaults below are used.

| Variable | Default   | Description                                  |
|----------|-----------|----------------------------------------------|
| `HOST`   | `0.0.0.0` | IP address the server binds to               |
| `PORT`   | `8080`    | TCP port the application listens on          |
| `DEBUG`  | `False`   | When `true`, enables debug mode with auto-reload and detailed error messages |