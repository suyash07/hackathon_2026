import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

es_user = os.getenv("ES_USER")
es_password = os.getenv("ES_PASSWORD")
if es_user is None and es_password is None:
    basic_auth = None
elif es_user is not None and es_password is not None:
    basic_auth = (es_user, es_password)
else:
    raise ValueError("ES_USER and ES_PASSWORD must be set together")

es = Elasticsearch(
    os.getenv("ES_URL"),
    basic_auth=basic_auth,
)

if __name__ == "__main__":
    print(es.info()["version"]["number"])
