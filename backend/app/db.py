# db.py
import os
import oracledb
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ORA_USER: str
    ORA_PASS: str
    ORA_DSN: str  # ex: host:port/service_name ou "(DESCRIPTION=...)"
    POOL_MIN: int = 1
    POOL_MAX: int = 10
    POOL_INC: int = 1

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

@lru_cache()
def get_pool():
    s = get_settings()
    pool = oracledb.create_pool(
        user=s.ORA_USER,
        password=s.ORA_PASS,
        dsn=s.ORA_DSN,
        min=s.POOL_MIN, max=s.POOL_MAX, increment=s.POOL_INC
    )
    return pool

def get_conn():
    pool = get_pool()
    return pool.acquire()
