# Lab 2 — Docker Containerization

## 1. Docker Best Practices Applied

### Non-Root User Implemetation

Created dedicated user `appuser` instead of running as root. Security - limits damage if container is compromised.

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

### Layer Caching Optimization


Ordered instructions to maximize Docker layer caching. Faster build - unchanged layers are reused from cache.

```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code last (changes frequently)
COPY app.py .
```

### .dockerignore File

Created `.dockerignore` to exclude unnecessary files. Smaller image size, faster builds, security (exclude secrets).

```
.git
__pycache__
*.pyc
.env
.vscode/
```

### Multi-Stage Build

Used builder pattern with two stages. Smaller final image - build tools excluded from runtime.

```dockerfile
FROM python:3.13-slim AS builder
# ... build dependencies
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
```

### Specific Base Image Version

Used `python:3.13-slim` instead of `python:latest`. Reproducibility - prevents breaking changes from updates.

### Health Check

Added HEALTHCHECK instruction. Container orchestration - Kubernetes/Docker can monitor health.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:5000/health || exit 1
```

## 2. Image Information & Decisions

### Base Image Choice

**Selected:** `python:3.13-slim`
**Justification:**

- `slim` variant: 45MB vs 350MB for full Python image
- Python 3.13: Latest stable version
- Security: Regular security updates from official Python Docker team
- Compatibility: Contains essential system libraries for Python packages

**Alternatives considered:**

- `python:3.13-alpine`: Even smaller (17MB) but musl libc can cause compatibility issues
- `python:3.13`: Full image (350MB) - unnecessarily large

### Final Image Size 

Final image size is 263MB. This is acceptable for FastAPI learning project, but there is a potential for optimization.

### Layer Structure

**Builder Stage**

Base python:3.13-slim

Virtual environment creation

Requirements copy

Package installation

**Runtime Stage** 

python:3.13-slim again

curl installation

Non-root user creation

Copy venv from builder

App code copy

Permissions fix

Configuration/env setup

### Optimization

- Multi-stage build
- .dockerignore
- Layer ordering
- Slim base image

## 3. Build & Run Process 

### Complete Build Output

```bash
docker build -t fastapi-lab-app:latest -f Dockerfile .
Step 22/24 : ENV DEBUG=False
 ---> Running in 33fe08aa5720
 ---> Removed intermediate container 33fe08aa5720
 ---> 5f5d31117ebd
Step 23/24 : HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD curl -f http://localhost:5000/health || exit 1
 ---> Running in 0dbc6a6e4352
 ---> Removed intermediate container 0dbc6a6e4352
 ---> 600a000fa952
Step 24/24 : CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
 ---> Running in 270f7a32ec5f
 ---> Removed intermediate container 270f7a32ec5f
 ---> cc6bae195ed2
Successfully built cc6bae195ed2
Successfully tagged fastapi-lab-app:latest
...
Step 22/24 : ENV DEBUG=False
 ---> Running in 33fe08aa5720
 ---> Removed intermediate container 33fe08aa5720
 ---> 5f5d31117ebd
Step 23/24 : HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD curl -f http://localhost:5000/health || exit 1
 ---> Running in 0dbc6a6e4352
 ---> Removed intermediate container 0dbc6a6e4352
 ---> 600a000fa952
Step 24/24 : CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
 ---> Running in 270f7a32ec5f
 ---> Removed intermediate container 270f7a32ec5f
 ---> cc6bae195ed2
Successfully built cc6bae195ed2
Successfully tagged fastapi-lab-app:latest
```

### Container Running Output

```bash
docker run -d -p 5000:5000 --name test-app fastapi-lab-app:latest
ec54aeed630c497775741259eab75cb6fb757e2d1a2faca3d2102328639cb77a
```

### Endpoint Testing

```bash
curl http://localhost:5000/
```

```
{"service":{"name":"devops-info-request"
"version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"4fc82f359ee1","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Fri, 30 Jan 2026 11:42:40 +0000","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":17,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T15:05:57.042Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

```bash
curl http://localhost:5000/health
```

```
{"status":"healthy","timestamp":"2026-02-04T15:06:06.033Z","uptime_seconds":26}
```

### Docker Hub Repository

**URL:** https://hub.docker.com/repository/docker/flowelx/devops-core-course/general

## 4. Technical Analysis

### Dockerfile Design Logic 

- Multi-stage build
- Layer ordering
- Virtual environment

### Layer Order

**Current order (optimized):**

1. System packages (rare changes)
2. Python dependencies (occasional changes)
3. App code (frequent changes)

If reversed: App code changes would invalidate all subsequent layers, causing full rebuilds.

### Security Measures

1. Non-root user (appuser) 
2. Minimal base image
3. No secrets in image
4. Health checks

### .dockerignore Benefits

- Faster builds
- Smaller images
- Security

## 5. Challenges & Solutions

### Challenge: Image Size Optimization

**Optimization Steps:**

1. Changed from `python:3.13` to `python:3.13-slim`
2. Added multi-stage build
3. Added `.dockerignore`
4. Used `--no-cache-dir` in pip

**What I learned:**
Docker layer caching is powerful. Proper ordering can save minutes per build. Non-root user is basic but essential. Smaller images = faster deployment.