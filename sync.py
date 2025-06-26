import os
import json
from pathlib import Path
from uuid import UUID
import weaviate
from weaviate.util import generate_uuid5  # Generate a deterministic ID
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
# from dotenv import load_dotenv

# load_dotenv()

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers={'X-OpenAI-Api-key': openai_api_key}
)

collection_name = "QAEntry"
tooltip_collection_name = "Tooltip"

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
                Property(name="tags", data_type=DataType.TEXT_ARRAY)
            ]
        )
        print(f"Created collection '{collection_name}'")

def upload_entry(entry, source):
    question = entry.get("question", "").strip()
    answer = entry.get("answer", "").strip()
    tags = entry.get("tags", [])

    if not question or not answer:
        print("Skipping invalid entry (missing question or answer)")
        return

    properties = {
        "question": question,
        "answer": answer,
        "tags": tags,
        "source": source
    }

    collection = client.collections.get(collection_name)
    uuid = generate_uuid5(properties['question'])
    try:
        collection.data.insert(
            properties=properties,
            uuid=uuid
        )
    except weaviate.exceptions.UnexpectedStatusCodeException as e:
        # If already exists, update the entry
        if "already exists" in str(e):
            print(f"Entry exists, updating: {question[:50]}...")
            collection.data.update(
                uuid=uuid,
                properties=properties
            )
        else:
            print(f"Error inserting entry: {e}")

def sync_qas():
    try:
        ensure_schema()
        docs_dir = Path(__file__).resolve().parent / "docs" / "faq"
        json_files = list(docs_dir.glob("*.json"))

        for file_path in json_files:
            with file_path.open(encoding="utf-8") as f:
                try:
                    qa_entries = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Skipping {file_path.name} due to JSON error: {e}")
                    continue

            for entry in qa_entries:
                try:
                    upload_entry(entry, str(file_path.relative_to(docs_dir)))
                    print(f"Uploaded Q&A: {entry.get('question', '')[:50]}...")
                except Exception as e:
                    print(f"Error uploading entry {entry}: {e}")

    finally:
        print("Finished syncing Q&A entries.")

def ensure_tooltip_schema():
    try:
        collection = client.collections.get(tooltip_collection_name)
        print(f"Collection '{tooltip_collection_name}' already exists")
    except weaviate.exceptions.UnexpectedStatusCodeException:
        client.collections.create(
            name=tooltip_collection_name,
            vectorizer_config=Configure.Vectorizer.text2vec_openai(),
            properties=[
                Property(name="term", data_type=DataType.TEXT),
                Property(name="headline", data_type=DataType.TEXT),
                Property(name="definition", data_type=DataType.TEXT),
                Property(name="link", data_type=DataType.TEXT)
            ]
        )
        print(f"Created collection '{tooltip_collection_name}'")

def upload_tooltip(entry):
    term = entry.get("term", "").strip()
    headline = entry.get("headline", "").strip()
    definition = entry.get("definition", "").strip()
    link = entry.get("link", "").strip() if "link" in entry else None

    if not term or not definition:
        print("Skipping invalid tooltip (missing term or definition)")
        return

    properties = {
        "term": term,
        "headline": headline,
        "definition": definition,
        "link": link
    }

    collection = client.collections.get(tooltip_collection_name)
    uuid = generate_uuid5(properties['term'])
    try:
        collection.data.insert(
            properties=properties,
            uuid=uuid
        )
    except weaviate.exceptions.UnexpectedStatusCodeException as e:
        if "already exists" in str(e):
            print(f"Tooltip exists, updating: {term[:50]}...")
            collection.data.update(
                uuid=uuid,
                properties=properties
            )
        else:
            print(f"Error inserting tooltip: {e}")

def sync_tooltips():
    try:
        ensure_tooltip_schema()
        tooltips_path = Path(__file__).resolve().parent / "docs" / "tooltips.json"
        if not tooltips_path.exists():
            print(f"Tooltips file not found: {tooltips_path}")
            return

        with tooltips_path.open(encoding="utf-8") as f:
            try:
                tooltip_entries = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading tooltips.json: {e}")
                return

        for entry in tooltip_entries:
            try:
                upload_tooltip(entry)
                print(f"Uploaded Tooltip: {entry.get('term', '')[:50]}...")
            except Exception as e:
                print(f"Error uploading tooltip {entry}: {e}")

    finally:
        print("Finished syncing tooltips.")

if __name__ == "__main__":
    try:
        sync_qas()
        sync_tooltips()
    finally:
        client.close()
