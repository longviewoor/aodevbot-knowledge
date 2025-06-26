import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import weaviate
from weaviate.util import generate_uuid5
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
# from dotenv import load_dotenv

# load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class WeaviateSyncer:
    def __init__(self):
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.environ["WEAVIATE_URL"],
            auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
            headers={'X-OpenAI-Api-key': os.environ["OPENAI_API_KEY"]}
        )

    def ensure_collection(self, name: str, properties: List[Property]):
        try:
            self.client.collections.get(name)
            logging.info(f"Collection '{name}' already exists")
        except weaviate.exceptions.UnexpectedStatusCodeException:
            self.client.collections.create(
                name=name,
                vectorizer_config=Configure.Vectorizer.text2vec_openai(),
                properties=properties
            )
            logging.info(f"Created collection '{name}'")

    def upsert_entry(self, collection_name: str, properties: Dict[str, Any], uuid_key: str):
        collection = self.client.collections.get(collection_name)
        uuid = generate_uuid5(properties[uuid_key])
        try:
            collection.data.insert(properties=properties, uuid=uuid)
            logging.info(f"Inserted: {properties.get(uuid_key, '')[:50]}")
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            if "already exists" in str(e):
                collection.data.update(uuid=uuid, properties=properties)
                logging.info(f"Updated: {properties.get(uuid_key, '')[:50]}")
            else:
                logging.error(f"Error inserting: {e}")

    def sync_from_json(self, collection_name: str, schema_props: List[Property], json_path: Path, uuid_key: str):
        self.ensure_collection(collection_name, schema_props)
        if not json_path.exists():
            logging.warning(f"File not found: {json_path}")
            return
        try:
            with json_path.open(encoding="utf-8") as f:
                entries = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading {json_path.name}: {e}")
            return
        for entry in entries:
            self.upsert_entry(collection_name, entry, uuid_key)

    def close(self):
        self.client.close()

def main():
    syncer = WeaviateSyncer()
    try:
        # Q&A sync
        qa_props = [
            Property(name="question", data_type=DataType.TEXT),
            Property(name="answer", data_type=DataType.TEXT),
            Property(name="source", data_type=DataType.TEXT),
            Property(name="tags", data_type=DataType.TEXT_ARRAY)
        ]
        docs_dir = Path(__file__).resolve().parent / "docs" / "faq"
        for file_path in docs_dir.glob("*.json"):
            syncer.sync_from_json("QAEntry", qa_props, file_path, "question")

        # Tooltip sync
        tooltip_props = [
            Property(name="term", data_type=DataType.TEXT),
            Property(name="headline", data_type=DataType.TEXT),
            Property(name="definition", data_type=DataType.TEXT),
            Property(name="link", data_type=DataType.TEXT)
        ]
        tooltip_path = Path(__file__).resolve().parent / "docs" / "tooltips.json"
        syncer.sync_from_json("Tooltip", tooltip_props, tooltip_path, "term")
    finally:
        syncer.close()

if __name__ == "__main__":
    main()
