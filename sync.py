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

# Setup clients
openai = OpenAI(api_key=openai_api_key)
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
    answer_parts = []
    
    # Debug: print tokens to understand structure
    print("=== DEBUG: Token structure ===")
    for i, token in enumerate(tokens):
        print(f"{i}: type={token.type}, tag={getattr(token, 'tag', 'None')}, content={getattr(token, 'content', 'None')[:50]}...")
    print("=== END DEBUG ===")
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Check for h3 heading start
        if token.type == 'heading_open' and token.tag == 'h3':
            # Save previous Q&A if exists
            if question and answer_parts:
                qas.append((question, "\n".join(answer_parts).strip()))
            
            # Get the question text from the next inline token
            if i + 1 < len(tokens) and tokens[i + 1].type == 'inline':
                question = tokens[i + 1].content.strip()
                answer_parts = []
            
            # Skip to after heading_close
            i += 2  # Skip inline and heading_close
            
        # Collect answer content (everything that's not a heading)
        elif token.type == 'inline' and question is not None:
            content = token.content.strip()
            if content:
                answer_parts.append(content)
        
        i += 1
    
    # Add the last Q&A pair
    if question and answer_parts:
        qas.append((question, "\n".join(answer_parts).strip()))
    
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

        print(f"Found {len(md_files)} markdown files in {docs_dir}")

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
