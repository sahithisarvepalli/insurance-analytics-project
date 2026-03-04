
import os, yaml, logging
from sqlalchemy import create_engine
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def load_config(path='config/db.yaml'):
    raw = {}
    if os.path.exists(path):
        with open(path,'r') as fh:
            raw = yaml.safe_load(fh) or {}
    def expand(v):
        if isinstance(v,str) and v.startswith('${') and v.endswith('}'):
            return os.getenv(v[2:-1])
        return v
    return {k: expand(v) for k,v in raw.items()}

def get_engine():
    cfg = load_config()
    url = os.getenv('DATABASE_URL') or cfg.get('engine_url')
    if not url:
        host = os.getenv('DB_HOST', cfg.get('host','localhost'))
        port = os.getenv('DB_PORT', cfg.get('port',5432))
        user = os.getenv('DB_USER', cfg.get('user','postgres'))
        pwd  = os.getenv('DB_PASS', cfg.get('password','postgres'))
        db   = os.getenv('DB_NAME', cfg.get('database','insurdb'))
        url = f'postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}'
    logger.info(f'Using engine URL: {url}')
    return create_engine(url)
