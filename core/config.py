
# Конфигурация подключения
POSTGRES_CONFIG = {
    "user": "postgres",
    "password": "4585",
    "host": "localhost",
    "port": "5433",
    "database": "coffee"
}


SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
ASYNCPG_DATABASE_URL = f"postgres://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
