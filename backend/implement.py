import os
import json
import subprocess
import re
from rag import call_claude
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma


CHROMA_PATH = "./chroma_db"
REPO_PATH = "../data/repo"


def get_relevant_context(ticket: str):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    results = db.similarity_search_with_score(ticket, k=8)

    context_parts = []

    for doc, score in results:
        source = doc.metadata.get("source", "Unknown source")
        content = doc.page_content

        context_parts.append(
            f"Source: {source}\n\n{content}"
        )

    return "\n\n---\n\n".join(context_parts)


def implement_ticket(ticket: str, auto_apply: bool = False):
    context = get_relevant_context(ticket)

    prompt = f"""
You are a senior software engineer implementing a Jira ticket.

Use only the repository context below.

Your job:
1. Understand the ticket
2. Identify files that likely need changes
3. Propose exact code changes
4. Return output as valid JSON only

Important rules:
- Do not invent files unless clearly marked as new files.
- Do not remove unrelated code.
- Prefer small, focused changes.
- Return raw JSON only.
- Do not wrap the JSON in markdown.
- Do not use ```json.
- Do not include explanation before or after the JSON.

JSON shape:
{{
  "summary": "short summary",
  "filesToModify": [
    {{
      "path": "relative/path/to/file",
      "reason": "why this file changes",
      "changeType": "modify | create",
      "proposedContent": "full updated file content"
    }}
  ],
  "testPlan": [
    "test step 1",
    "test step 2"
  ],
  "risks": [
    "risk or unknown"
  ]
}}

Repository context:
{context}

Jira ticket:
{ticket}
"""

    response_text = call_claude(prompt)

    try:
        implementation = parse_claude_json(response_text)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Claude did not return valid JSON.",
            "rawResponse": response_text
        }

    if auto_apply:
        safe_summary = re.sub(
            r"[^a-zA-Z0-9-]+",
            "-",
            implementation.get("summary", "jira-change").lower()
        ).strip("-")

        branch_name = f"ai/{safe_summary[:40]}"

        branch_result = create_branch(branch_name)

        apply_changes(implementation)
        diff = get_git_diff()

        test_result = run_command(["npm", "test"])
        lint_result = run_command(["npm", "run", "lint"])

        commit_result = commit_changes(
            f"Implement Jira ticket: {implementation.get('summary', 'AI generated change')}"
        )
    else:
        diff = ""
        branch_result = None
        test_result = None
        lint_result = None
        commit_result = None
                

    return {
        "success": True,
        "autoApplied": auto_apply,
        "implementation": implementation,
        "diff": diff,
        "branchResult": branch_result,
        "testResult": test_result,
        "lintResult": lint_result,
        "commitResult": commit_result
    }


def apply_changes(implementation):
    for file_change in implementation.get("filesToModify", []):
        relative_path = file_change["path"]
        proposed_content = file_change["proposedContent"]

        if not is_safe_path(relative_path):
            raise ValueError(f"Unsafe path: {relative_path}")
    
        full_path = os.path.join(REPO_PATH, relative_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(proposed_content)

def get_git_diff():
    result = subprocess.run(
        ["git", "diff"],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    return result.stdout


def run_command(command: list[str]):
    result = subprocess.run(
        command,
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    return {
        "command": " ".join(command),
        "exitCode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def create_branch(branch_name: str):
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    return {
        "command": f"git checkout -b {branch_name}",
        "exitCode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def commit_changes(message: str):
    add_result = subprocess.run(
        ["git", "add", "."],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    if add_result.returncode != 0:
        return {
            "success": False,
            "step": "git add",
            "stdout": add_result.stdout,
            "stderr": add_result.stderr
        }

    commit_result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    return {
        "success": commit_result.returncode == 0,
        "step": "git commit",
        "stdout": commit_result.stdout,
        "stderr": commit_result.stderr
    }

def is_safe_path(path: str):
    blocked = [".env", "node_modules", ".git", "package-lock.json"]

    if path.startswith("/") or ".." in path:
        return False

    if any(blocked_part in path for blocked_part in blocked):
        return False

    return True

def parse_claude_json(response_text: str):
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return json.loads(cleaned)