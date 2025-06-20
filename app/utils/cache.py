import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def cache_signal(key, value):
    r.set(key, value)

def get_cached_signal(key):
    return r.get(key) 