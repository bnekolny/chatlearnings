import hashlib
import json
from datetime import date
from google.cloud import storage
import os
from typing import List

class GCSFactStorage:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    @staticmethod
    def hash_string(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()

    def get_gcs_prefix(self, email_hash: str, topic_hash: str) -> str:
        return f"{email_hash}/{topic_hash}/"

    def get_gcs_path(self, email_hash: str, topic_hash: str, dt: date) -> str:
        return f"{email_hash}/{topic_hash}/{dt.isoformat()}.json"

    def list_facts(self, email_hash: str, topic_hash: str) -> List[dict]:
        prefix = self.get_gcs_prefix(email_hash, topic_hash)
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        facts = []
        for blob in blobs:
            content = blob.download_as_text()
            try:
                facts.append(json.loads(content))
            except Exception:
                facts.append({"raw": content})
        return facts

    def write_fact(self, email_hash: str, topic_hash: str, dt: date, content: str):
        path = self.get_gcs_path(email_hash, topic_hash, dt)
        blob = self.bucket.blob(path)
        blob.upload_from_string(json.dumps({"content": content}))
