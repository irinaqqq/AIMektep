import ssl
from celery import Celery, signals

from core.dependencies import get_config
from core.logger import logger, setup_logging

@signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    setup_logging()

logger.debug("Creating celery app")

config = get_config()
redis_url = config.REDIS_URL

celery_app = Celery(
    'backend',
    broker=redis_url,
    backend=redis_url,
    include=[
        'services.scheduler.tasks',
    ]
)

if redis_url.startswith("rediss://"):
    ssl_config = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": "/certs/ca.pem",
    }

    celery_app.conf.update(
        broker_use_ssl=ssl_config,
        redis_backend_use_ssl=ssl_config,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        broker_connection_retry_on_startup=True
    )
