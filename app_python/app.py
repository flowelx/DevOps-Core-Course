import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        }
        
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'path'):
            log_record['path'] = record.path
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_record['client_ip'] = record.client_ip
            
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

app = FastAPI()

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

APP_START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех запросов"""
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info("Request started", extra={
        'method': request.method,
        'path': request.url.path,
        'client_ip': client_ip
    })
    
    response = await call_next(request)
    
    logger.info("Request completed", extra={
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'client_ip': client_ip
    })
    
    return response


def get_uptime():
    """Calculate application runtime"""
    delta = datetime.now(timezone.utc) - APP_START_TIME
    seconds = int(delta.total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        'seconds': seconds,
        'human': f"{hours}h {minutes}m"
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Application started", extra={
        'host': HOST,
        'port': PORT,
        'hostname': socket.gethostname()
    })


@app.get('/')
async def get_service_info(request: Request):
    client_ip = request.client.host if request.client else '127.0.0.1'
    
    service_info = {
        'name': 'devops-info-request',
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'uptime': get_uptime()['human']
    }

    logger.info("Home page accessed", extra={
        'client_ip': client_ip
    })

    return service_info


@app.get('/health')
async def health_check(request: Request):
    logger.info("Health check", extra={
        'client_ip': request.client.host if request.client else 'unknown'
    })

    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@app.get('/error')
async def test_error(request: Request):
    client_ip = request.client.host if request.client else 'unknown'
    
    logger.error("Test error", extra={
        'client_ip': client_ip,
        'error_type': 'test_error'
    })
    
    return JSONResponse(
        status_code=500,
        content={'error': 'Test error'}
    )


if __name__ == '__main__':
    logger.info(f'Starting server on {HOST}:{PORT}')
    uvicorn.run(
        'app:app',
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
