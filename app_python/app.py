import os
import socket
import platform
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

APP_START_TIME = datetime.now(timezone.utc)


def get_uptime():
    """Calculate application runtime"""
    delta = datetime.now(timezone.utc) - APP_START_TIME
    seconds = int(delta.total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, "
                 f"{minutes} minute{'s' if minutes != 1 else ''}"
    }


@app.get('/')
async def get_service_info(request: Request):
    """
    Root endpoint returning comprehensive service and system information.
    
    Returns:
        dict: JSON containing service, system, runtime, and request information.
    """
    logger.info(
        f"GET / from {request.client.host if request.client else 'unknown'}"
    )
    
    service_info = {
        'name': 'devops-info-request',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'FastAPI'
    }

    system_info = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }

    uptime = get_uptime()
    runtime_info = {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(timezone.utc).isoformat() + 'Z',
        'timezone': 'UTC'
    }

    client_ip = request.client.host if request.client else '127.0.0.1'
    request_info = {
        'client_ip': client_ip,
        'user_agent': request.headers.get('user-agent', 'uknown'),
        'method': request.method,
        'path': request.url.path
    }

    endpoints = [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'}
    ]

    response = {
        'service': service_info,
        'system': system_info,
        'runtime': runtime_info,
        'request': request_info,
        'endpoints': endpoints
    }

    return response


@app.get('/health')
async def health_check(request: Request):
    """
    Health check endpoint for service monitoring.
    
    Returns:
        dict: Service health status with timestamp and uptime.
    """
    logger.info('Health check requested')

    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'uptime_seconds': get_uptime()['seconds']
    }


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    """Handle 404 errors: page not found"""

    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 errors: internal server errors"""

    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == '__main__':
    logger.info(f'Starting server on {HOST}:{PORT}')

    uvicorn.run(
        'app:app',
        host=HOST,
        port=PORT,
        reload=DEBUG
    )