from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import os
import requests

load_dotenv()

def call_claude(prompt: str):
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return "ANTHROPIC_API_KEY is missing. Add it to backend/.env and restart the server."

    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1500,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        return f"Claude API error {response.status_code}: {response.text}"

    data = response.json()
    return data["content"][0]["text"]

CHROMA_PATH = "./chroma_db"

PROMPT_TEMPLATE = """
You are a senior software engineering assistant.

Use only the provided context to answer the question.

Rules:
- Do not make up files, functions, APIs, or behavior.
- If the answer is not in the context, say: "I could not find that in the indexed files."
- When answering about code, mention the exact files and functions.
- When helpful, explain how the files connect to each other.
- Keep the answer practical and concise.
- Format the answer in clean Markdown with headings, bullet points, and short paragraphs.

Context:
{context}

Question:
{question}
"""

def ask_rag(question: str, mode: str = "general"):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    results = db.similarity_search_with_score(question, k=5)

    if not results:
        return {
            "answer": "I could not find that in the indexed files.",
            "sources": []
        }

    seen_chunks = set()
    unique_results = []

    for doc, score in results:
        source = doc.metadata.get("source", "Unknown source")
        content = doc.page_content.strip()
        unique_key = f"{source}:{content}"

        if unique_key not in seen_chunks:
            seen_chunks.add(unique_key)
            unique_results.append((doc, score))

    context = "\n\n---\n\n".join(
        [
            f"Source: {doc.metadata.get('source')}\n{doc.page_content}"
            for doc, _score in unique_results
        ]
    )

    prompt = ChatPromptTemplate.from_template(get_prompt_for_mode(mode))

    model = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0
    )

    chain = prompt | model

    response = chain.invoke({
        "context": context,
        "question": question
    })

    sources = []

    for doc, _score in unique_results:
        source = doc.metadata.get("source")
        if source and source not in sources:
            sources.append(source)

    return {
        "answer": response.content,
        "sources": sources
    }

# def ask_rag(question: str):
#     embeddings = HuggingFaceEmbeddings(
#         model_name="sentence-transformers/all-MiniLM-L6-v2"
#     )

#     db = Chroma(
#         persist_directory=CHROMA_PATH,
#         embedding_function=embeddings
#     )

#     results = db.similarity_search_with_score(question, k=5)

#     if not results:
#         return {
#             "answer": "I could not find that in the indexed files.",
#             "sources": []
#         }

#     answer_parts = []

#     for doc, score in results:
#         source = doc.metadata.get("source")
#         content = doc.page_content
#         answer_parts.append(
#             f"Source: {source}\n\nRelevant content:\n{content}\n"
#         )

#     sources = list(set(
#         doc.metadata.get("source")
#         for doc, _score in results
#     ))

#     return {
#         "answer": "\n---\n".join(answer_parts),
#         "sources": sources
#     }

def get_prompt_for_mode(mode: str):
    if mode == "files":
        return """
You are a senior codebase navigation assistant.

Use only the context below.

The user wants to find relevant files in this repository.

Return the answer in clean Markdown:

## Most Relevant Files

For each file, include:
- File path
- Why it matters
- What to inspect inside it

## Suggested Reading Order

List the files in the order a developer should read them.

## Confidence

Mention if the context is incomplete.

Do not invent files that are not in the context.

Context:
{context}

Question:
{question}
"""

    if mode == "jira":
        return """
You are a senior software engineer helping convert a Jira ticket into an implementation plan.

Use only the context below.

Return clean Markdown with these sections:

## Ticket Summary

Summarize the requested change.

## Relevant Files

List files from the context and explain why each matters.

## Implementation Plan

Give step-by-step implementation tasks.

## Code Change Suggestions

Mention specific functions, components, or modules that may need changes.

## Test Plan

List unit, integration, and UI test cases.

## Risks / Unknowns

Mention anything missing from the available context.

Rules:
- Do not invent files.
- Do not claim the change is already implemented unless the context proves it.
- Be practical and concise.

Context:
{context}

Ticket:
{question}
"""

    if mode == "tests":
        return """
You are a senior frontend testing assistant.

Use only the context below.

Return:
1. What behavior should be tested
2. Suggested test files
3. Test cases
4. Edge cases

Context:
{context}

Question:
{question}
"""

    return PROMPT_TEMPLATE