from celery import Celery
from backend.src.config import settings

# Celery configuration
celery_app = Celery(
    'engels',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['backend.src.tasks']
)

# Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routing for local vs MCP processing
celery_app.conf.task_routes = {
    'backend.src.tasks.process_document_local': {'queue': 'local_ollama'},
    'backend.src.tasks.process_document_mcp': {'queue': 'mcp_external'},
    'backend.src.tasks.extract_entities': {'queue': 'local_ollama'},
    'backend.src.tasks.anonymize_and_send': {'queue': 'mcp_external'},
}
