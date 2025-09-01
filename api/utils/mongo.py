import os
from pymongo import MongoClient
from utils.config import get_settings
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    settings = get_settings()
    db_uri = os.environ.get('DB_CONNECTION', getattr(settings, 'db_connection', None))
    if not db_uri:
        raise ValueError('DB_CONNECTION não encontrado nas variáveis de ambiente ou configurações')
    client = MongoClient(db_uri)
    return client
