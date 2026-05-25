from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import ask_rag
from pydantic import BaseModel
from typing import Optional
from implement import implement_ticket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    mode: str = "general"

class ImplementRequest(BaseModel):
    ticket: str
    auto_apply: bool = False

class ApplyRequest(BaseModel):
    implementation: dict

@app.get("/")
def home():
    return {"message": "RAG Repo Assistant is running"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    return ask_rag(request.question, request.mode)

@app.post("/implement")
def implement_jira(request: ImplementRequest):
    return implement_ticket(
        ticket=request.ticket,
        auto_apply=request.auto_apply
    )

@app.post("/apply")
def apply_implementation(request: ApplyRequest):
    apply_changes(request.implementation)
    return {"success": True}
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