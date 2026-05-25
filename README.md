# RAG Repo Assistant

A Claude-powered Retrieval-Augmented Generation app that answers questions about documentation and source code.

## Features

- Reads docs and source files
- Splits files into searchable chunks
- Stores embeddings in ChromaDB
- Uses Claude to answer questions from retrieved context
- Shows source files
- Supports Jira-ticket implementation planning
- Supports test-plan generation
- Includes simple retrieval evaluation

## Tech Stack

- React
- TypeScript
- FastAPI
- Python
- LangChain
- ChromaDB
- sentence-transformers
- Claude / Anthropic API

## Example Questions

- Where is payment handled?
- Which file renders checkout?
- Add PayPal as a payment option.
- What tests should I write for checkout?