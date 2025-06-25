# ✨ AO DevBot Knowledge Base

This repository contains a structured collection of **Question & Answer (Q&A)** entries used to power an AI system backed by Weaviate and RAG (Retrieval-Augmented Generation).

Each commit to this repository automatically syncs new or updated Q&A entries into our vector database using GitHub Actions and OpenAI embeddings. The AI backend uses this data to answer user queries with high relevance.

## 📄 Format Guidelines

All Q&A content should be written in **JSON** files (`.json`) located in the `docs/` directory. Each file contains an array of Q&A entries.

### ✅ Example Format

```json
[
  {
    "question": "What is AO?",
    "answer": "AO is a decentralized computer network built on top of Arweave that enables developers to create scalable, permanent applications.",
    "tags": ["ao", "arweave", "general"]
  },
  {
    "question": "What is Arweave?",
    "answer": "Arweave is a blockchain-like protocol designed for permanent data storage. It allows users to store data indefinitely by incentivizing miners to maintain the network.",
    "tags": ["arweave", "blockchain", "storage"]
  }
]
```

- Each entry must contain:
  - `"question"`: The question string (required)
  - `"answer"`: The answer string (required)
  - `"tags"`: An array of keywords (optional but recommended)

## 🏷️ Tagging Guidelines

Tags help categorize and filter content. They improve search relevance and allow topic-based filtering in the AI system.

- Use lowercase keywords.
- Keep tags relevant and limited (2–5 tags is ideal).
- Use consistent terminology across entries (e.g., "arweave", not "Arweave").

## ✍️ Content Contribution Guidelines

To ensure high quality and useful AI responses, please follow these rules:

### ✅ Do
- ✅ Keep answers **short and focused** (1–3 paragraphs, ideally 100–300 tokens).
- ✅ Use **clear language** — prioritize helpfulness and accuracy.
- ✅ Break large concepts into **multiple Q&As** if needed.

### ❌ Don’t
- ❌ Don’t write overly long answers (>400 words).
- ❌ Don’t include multiple questions in one entry.
- ❌ Don’t add unrelated metadata or extra fields.
