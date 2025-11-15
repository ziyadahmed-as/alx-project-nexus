from django.conf import settings
import redis
from redis.exceptions import ConnectionError

def get_redis_connection():
    try:
        return redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            password=settings.REDIS_CONFIG['PASSWORD'] or None,
            ssl=settings.REDIS_CONFIG['SSL'],
            socket_timeout=5,
            socket_connect_timeout=5,
            decode_responses=True
        )
    except ConnectionError:
        return None