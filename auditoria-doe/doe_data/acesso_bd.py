from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from doe_data.settings_bd import Settings
import certifi

settings = Settings()

def get_engine():
    # Configure SSL context
    connect_args = {
        'sslmode': 'disable',
    }
    
    return create_engine(
        make_url(settings.DATABASE_URL).set(host=settings.HOST),
        connect_args=connect_args
    )