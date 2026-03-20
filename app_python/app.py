import os
import socket
import platform
import logging
import json
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

# Очищаем registry при запуске (чтобы избежать дубликатов)
# Это решит проблему с Duplicated timeseries
for collector in list(REGISTRY._collector_to_names):
    REGISTRY.unregister(collector)

# Метрики с уникальными именами
http_requests_counter = Counter(
    'app_http_requests_total', 
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration = Histogram(
    'app_http_request_duration_seconds', 
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests_gauge = Gauge(
    'app_active_requests', 
    'Active requests count'
)

external_api_calls_counter = Counter(
    'app_external_api_calls_total', 
    'External API calls count',
    ['api_name']
)

system_info_duration_histogram = Histogram(
    'app_system_info_collection_seconds', 
    'System info collection time in seconds'
)

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

# Используем lifespan контекстный менеджер вместо on_event (решает deprecation warning)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application started", extra={
        'host': HOST,
        'port': PORT,
        'hostname': socket.gethostname()
    })
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(lifespan=lifespan)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

APP_START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование и метрики всех запросов"""
    client_ip = request.client.host if request.client else "unknown"
    
    # Увеличиваем счетчик активных запросов
    active_requests_gauge.inc()
    
    # Засекаем время начала запроса
    start_time = time.time()
    
    logger.info("Request started", extra={
        'method': request.method,
        'path': request.url.path,
        'client_ip': client_ip
    })
    
    try:
        response = await call_next(request)
        
        # Обновляем метрики
        duration = time.time() - start_time
        
        # Считаем запросы по методу, endpoint'у и статусу
        http_requests_counter.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code)
        ).inc()
        
        # Записываем длительность
        http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        logger.info("Request completed", extra={
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration': f"{duration:.3f}s",
            'client_ip': client_ip
        })
        
        return response
    finally:
        # Уменьшаем счетчик активных запросов
        active_requests_gauge.dec()


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


@app.get('/')
async def get_service_info(request: Request):
    client_ip = request.client.host if request.client else '127.0.0.1'
    
    # Измеряем время сбора системной информации
    start_time = time.time()
    
    service_info = {
        'name': 'devops-info-request',
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'uptime': get_uptime()['human']
    }
    
    # Записываем время сбора информации
    system_info_duration_histogram.observe(time.time() - start_time)
    
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
    
    # Пример вызова внешнего API (для демонстрации метрики)
    external_api_calls_counter.labels(api_name='test_api').inc()
    
    logger.error("Test error", extra={
        'client_ip': client_ip,
        'error_type': 'test_error'
    })
    
    return JSONResponse(
        status_code=500,
        content={'error': 'Test error'}
    )


@app.get('/metrics')
async def get_metrics(request: Request):
    """Endpoint для Prometheus метрик"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )


if __name__ == '__main__':
    logger.info(f'Starting server on {HOST}:{PORT}')
    uvicorn.run(
        'app:app',
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
