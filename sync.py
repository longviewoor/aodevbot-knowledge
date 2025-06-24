import os
from pathlib import Path
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
from openai import OpenAI
from markdown_it import MarkdownIt

# Setup clients
openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Best practice: store your credentials in environment variables
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers={'X-OpenAI-Api-key': openai_api_key}
)

md = MarkdownIt()

# Ensure schema is in place
def ensure_schema():
    try:
        # Check if collection exists
        collection = client.collections.get("QAEntry")
        print("Collection 'QAEntry' already exists")
    except weaviate.exceptions.UnexpectedStatusCodeException:
        # Create collection if it doesn't exist
        client.collections.create(
            name="QAEntry",
            vectorizer_config=Configure.Vectorizer.none(),  # We'll provide our own vectors
            properties=[
                weaviate.classes.config.Property(name="question", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="answer", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="source", data_type=weaviate.classes.config.DataType.TEXT),
                weaviate.classes.config.Property(name="tags", data_type=weaviate.classes.config.DataType.TEXT_ARRAY)
            ]
        )
        print("Created collection 'QAEntry'")

# Embed text using OpenAI
def embed(text: str):
    res = openai.embeddings.create(model="text-embedding-3-small", input=[text])
    return res.data[0].embedding

# Parse Q&A pairs from markdown
def parse_qa_markdown(content: str):
    tokens = md.parse(content)
    qas = []
    question = None
    answer_lines = []

    for token in tokens:
        if token.tag == 'h3':
            if question:
                qas.append((question, "\n".join(answer_lines)))
            question = token.content.strip()
            answer_lines = []
        elif token.type == 'inline':
            answer_lines.append(token.content.strip())

    if question:
        qas.append((question, "\n".join(answer_lines)))

    return qas

# Extract tags and clean answer content
def extract_tags_and_answer(answer_lines):
    tags = []
    content_lines = []

    for line in answer_lines:
        if line.lower().startswith("**tags**:"):
            tag_line = line.split(":", 1)[1]
            tags = [t.strip() for t in tag_line.split(",")]
        else:
            content_lines.append(line.strip())

    return tags, "\n".join(content_lines)

# Upload to Weaviate
def upload_entry(question, raw_answer, source):
    answer_lines = raw_answer.splitlines()
    tags, clean_answer = extract_tags_and_answer(answer_lines)
    vector = embed(question)

    collection = client.collections.get("QAEntry")
    
    collection.data.insert(
        properties={
            "question": question,
            "answer": clean_answer,
            "tags": tags,
            "source": source
        },
        vector=vector
    )

# Main sync function
def sync_qas():
    try:
        ensure_schema()
        docs_dir = Path(__file__).resolve().parent / "docs"
        md_files = list(docs_dir.glob("*.md"))

        for file_path in md_files:
            content = file_path.read_text(encoding="utf-8")
            qas = parse_qa_markdown(content)

            for question, raw_answer in qas:
                upload_entry(question, raw_answer, str(file_path.relative_to(docs_dir)))
                print(f"Uploaded Q&A: {question[:50]}...")

    finally:
        client.close()

if __name__ == "__main__":
    sync_qas()
