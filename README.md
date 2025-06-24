# ✨ AO DevBot Knowledge Base

This repository contains a structured collection of **Question & Answer (Q&A)** entries used to power an AI system backed by Weaviate and RAG (Retrieval-Augmented Generation).

Each commit to this repository automatically syncs new or updated Q&A entries into our vector database using GitHub Actions and OpenAI embeddings. The AI backend uses this data to answer user queries with high relevance.

## 📄 Format Guidelines

All Q&A content should be written in **Markdown** files (`.md`) located in the `docs/` directory. Each question should start with a level-3 heading (`###`), followed by its answer in plain text or Markdown format.

### ✅ Example Format

```
### What is AO?

AO is a decentralized computer network built on top of Arweave that enables developers to create scalable, permanent applications ...
```

- Each Q&A pair must start with `### Question`.
- The answer should immediately follow the heading.

## ✍️ Content Contribution Guidelines

To ensure high quality and useful AI responses, please follow these rules:

### ✅ Do
- ✅ Keep answers **short and focused** (1–3 paragraphs, ideally 100–300 tokens).
- ✅ Use **clear language** — prioritize helpfulness and accuracy.
- ✅ Break large concepts into **multiple Q&As** if needed.
- ✅ Use simple Markdown formatting (`**bold**`, lists, links) if it improves clarity.

### ❌ Don’t
- ❌ Don’t write overly long answers (>400 words).
- ❌ Don’t include multiple questions in one heading.
- ❌ Don’t include unrelated content or metadata.

## 📁 File Structure

Place your Q&A Markdown files in the `docs/` folder:

```
docs/
├── faq-product.md
├── faq-security.md
└── faq-troubleshooting.md
```

You can organize by topic (e.g. `faq-auth.md`, `faq-billing.md`).
