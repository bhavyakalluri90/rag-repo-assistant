from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import ask_rag

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


@app.get("/")
def home():
    return {"message": "RAG Repo Assistant is running"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    return ask_rag(request.question, request.mode)