from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.llm.local_model import (
    generate_response,
    search_knowledge,
    MODEL,
)


# --------------------------------------------------
# APP
# --------------------------------------------------

app = FastAPI(
    title="Jarvis API",
    description="API local para el asistente personal Jarvis",
    version="0.1.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

# Next.js normalmente corre en localhost:3000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# MODELOS
# --------------------------------------------------

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1
    )

    history: list[HistoryMessage] = []


class SourceResponse(BaseModel):
    source: str
    page: int
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[SourceResponse]


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "Jarvis",
        "status": "online",
        "model": MODEL
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "model": MODEL
    }


# --------------------------------------------------
# CHAT
# --------------------------------------------------

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:

        history = [
            {
                "role": item.role,
                "content": item.content
            }
            for item in request.history
        ]

        result = generate_response(
            user_message=request.message,
            history=history
        )

        return result

    except Exception as error:

        print(
            f"Error generando respuesta: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# BUSCAR EN PAPERS
# --------------------------------------------------

@app.post("/knowledge/search")
def knowledge_search(
    request: SearchRequest
):

    try:

        results = search_knowledge(
            request.query,
            n=request.limit
        )

        return {
            "query": request.query,
            "results": results
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )