import os
import socket
import platform
import logging
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

for collector in list(REGISTRY._collector_to_names):
    REGISTRY.unregister(collector)

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

def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config():
    config = {
        'application': {
            'name': os.getenv('APP_NAME', 'DevOps Info Service'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': '1.0.0',
            'framework': 'FastAPI'
        },
        'features': {
            'visits_counter': os.getenv('FEATURE_VISITS', 'true').lower() == 'true',
            'metrics_enabled': os.getenv('FEATURE_METRICS', 'true').lower() == 'true',
            'structured_logging': os.getenv('LOG_FORMAT', 'json') == 'json',
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        },
        'api': {
            'rate_limit': int(os.getenv('RATE_LIMIT', '100')),
            'timeout_seconds': int(os.getenv('TIMEOUT_SECONDS', '30')),
            'max_request_size_mb': int(os.getenv('MAX_REQUEST_SIZE_MB', '10'))
        },
        'monitoring': {
            'prometheus_enabled': os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true',
            'health_check_enabled': os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
            'metrics_path': os.getenv('METRICS_PATH', '/metrics')
        }
    }
    
    config_file = os.getenv('CONFIG_FILE', '/config/config.json')
    try:
        if Path(config_file).exists():
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config = deep_merge(config, file_config)
                logger.info(f"Loaded configuration from {config_file}")
    except Exception as e:
        logger.warning(f"Could not load config file {config_file}: {e}")
    
    return config

APP_CONFIG = load_config()

VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits.json')
visits_lock = threading.Lock()

def ensure_data_directory():
    data_dir = os.path.dirname(VISITS_FILE)
    try:
        os.makedirs(data_dir, exist_ok=True)
        test_file = os.path.join(data_dir, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"Data directory {data_dir} is writable")
        return True
    except Exception as e:
        logger.error(f"Cannot write to data directory {data_dir}: {e}")
        return False

def read_visits():
    try:
        if os.path.exists(VISITS_FILE):
            with open(VISITS_FILE, 'r') as f:
                data = json.load(f)
                count = data.get('visits', 0)
                logger.info(f"Loaded visits count from file: {count}")
                return count
        else:
            logger.info("Visits file not found, starting from 0")
    except (json.JSONDecodeError, IOError, PermissionError) as e:
        logger.error(f"Error reading visits file: {e}, starting from 0")
    return 0

def save_visits(count):
    try:
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        
        with open(VISITS_FILE, 'w') as f:
            json.dump({
                'visits': count,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }, f)
        
        logger.debug(f"Saved visits count to file: {count}")
    except (IOError, PermissionError) as e:
        logger.error(f"Error saving visits file: {e}")

def increment_visits():
    with visits_lock:
        current_count = read_visits()
        new_count = current_count + 1
        save_visits(new_count)
        logger.info(f"Visits count incremented to: {new_count}")
        return new_count

ensure_data_directory()
VISITS_COUNT = read_visits()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started", extra={
        'host': HOST,
        'port': PORT,
        'hostname': socket.gethostname(),
        'initial_visits': VISITS_COUNT
    })
    yield
    logger.info("Application shutting down", extra={
        'final_visits': read_visits()
    })

app = FastAPI(lifespan=lifespan)

if APP_CONFIG['application']['name']:
    app.title = APP_CONFIG['application']['name']

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
DEBUG = APP_CONFIG['features']['debug_mode']

APP_START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    active_requests_gauge.inc()
    
    start_time = time.time()
    
    logger.info("Request started", extra={
        'method': request.method,
        'path': request.url.path,
        'client_ip': client_ip
    })
    
    try:
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        http_requests_counter.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code)
        ).inc()
        
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
        active_requests_gauge.dec()


def get_uptime():
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
    current_visits = increment_visits() if APP_CONFIG['features']['visits_counter'] else 0
    
    client_ip = request.client.host if request.client else '127.0.0.1'
    
    start_time = time.time()
    
    service_info = {
        'service': APP_CONFIG['application'],
        'system': {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'uptime': get_uptime()['human']
        },
        'features': APP_CONFIG['features'],
        'visits': current_visits if APP_CONFIG['features']['visits_counter'] else None,
        'environment': APP_CONFIG['application']['environment']
    }
    
    system_info_duration_histogram.observe(time.time() - start_time)
    
    logger.info("Home page accessed", extra={
        'client_ip': client_ip,
        'visits_count': current_visits,
        'environment': APP_CONFIG['application']['environment']
    })

    return service_info


@app.get('/visits')
async def get_visits(request: Request):
    current_count = read_visits()
    
    logger.info("Visits endpoint accessed", extra={
        'client_ip': request.client.host if request.client else 'unknown',
        'visits_count': current_count
    })
    
    return {
        'visits': current_count,
        'last_updated': datetime.now(timezone.utc).isoformat()
    }


@app.get('/config')
async def get_config(request: Request):
    logger.info("Config endpoint accessed", extra={
        'client_ip': request.client.host if request.client else 'unknown'
    })
    
    return {
        'application': APP_CONFIG['application'],
        'features': APP_CONFIG['features'],
        'api': APP_CONFIG['api'],
        'monitoring': APP_CONFIG['monitoring']
    }


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
