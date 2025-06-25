import os
import json
from pathlib import Path
from uuid import UUID
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers={'X-OpenAI-Api-key': openai_api_key}
)

collection_name = "QuestionAnswer"

def ensure_schema():
    try:
        collection = client.collections.get(collection_name)
        print(f"Collection '{collection_name}' already exists")
    except weaviate.exceptions.UnexpectedStatusCodeException:
        client.collections.create(
            name=collection_name,
            vectorizer_config=Configure.Vectorizer.text2vec_openai(),
            properties=[
                Property(name="question", data_type=DataType.TEXT),
                Property(name="answer", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="tags", data_type=DataType.TEXT_ARRAY),
                Property(name="uuid", data_type=DataType.UUID),
            ]
        )
        print(f"Created collection '{collection_name}'")

def upload_entry(entry, source):
    question = entry.get("question", "").strip()
    answer = entry.get("answer", "").strip()
    tags = entry.get("tags", [])
    uuid = entry.get("uuid")

    if not question or not answer:
        print("Skipping invalid entry (missing question or answer)")
        return

    properties = {
        "question": question,
        "answer": answer,
        "tags": tags,
        "source": source,
        "uuid": uuid
    }

    collection = client.collections.get(collection_name)
    collection.data.insert(properties=properties)

def sync_qas():
    try:
        ensure_schema()
        docs_dir = Path(__file__).resolve().parent / "docs"
        json_files = list(docs_dir.glob("*.json"))

        for file_path in json_files:
            with file_path.open(encoding="utf-8") as f:
                try:
                    qa_entries = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Skipping {file_path.name} due to JSON error: {e}")
                    continue

            for entry in qa_entries:
                upload_entry(entry, str(file_path.relative_to(docs_dir)))
                print(f"Uploaded Q&A: {entry.get('question', '')[:50]}...")

    finally:
        client.close()

if __name__ == "__main__":
    sync_qas()
