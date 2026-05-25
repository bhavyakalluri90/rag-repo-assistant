from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

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
You are a senior codebase analysis assistant.

Use only the context below.

The user wants to know which files are relevant.

Return:
1. Relevant files
2. Why each file matters
3. What the user should inspect first

Context:
{context}

Question:
{question}
"""

    if mode == "jira":
        return """
You are a senior software engineer helping plan a Jira ticket.

Use only the context below.

Return:
1. Summary of the requested change
2. Relevant files
3. Step-by-step implementation plan
4. Test plan
5. Risks or unknowns

Do not invent files that are not in the context.

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