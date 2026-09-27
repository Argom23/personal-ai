from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.llm.local_model import (
    generate_response,
    generate_chat_title,
    is_meaningful_for_title,
    search_knowledge,
    MODEL,
)

from backend.database import (
    create_chat,
    list_chats,
    get_chat,
    get_chat_messages,
    get_chat_history,
    save_message,
    delete_chat,
    update_chat_title,
)


# --------------------------------------------------
# APP
# --------------------------------------------------

app = FastAPI(
    title="Jarvis API",
    description="API local para el asistente personal Jarvis",
    version="0.2.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

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

    history: list[HistoryMessage] = Field(
        default_factory=list
    )


class SourceResponse(BaseModel):
    source: str
    page: int
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[SourceResponse]


class CreateChatRequest(BaseModel):
    title: str = "Nuevo chat"


class UpdateChatTitleRequest(BaseModel):
    title: str = Field(
        min_length=1
    )


class SendMessageRequest(BaseModel):
    message: str = Field(
        min_length=1
    )


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


# --------------------------------------------------
# ROOT / HEALTH
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
# CHAT ANTIGUO
#
# Lo mantenemos para que el frontend actual
# siga funcionando mientras hacemos el historial.
# --------------------------------------------------

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):
    try:
        history = [
            {
                "role": item.role,
                "content": item.content
            }
            for item in request.history
        ]

        return generate_response(
            user_message=request.message,
            history=history
        )

    except Exception as error:
        print(
            f"Error generando respuesta: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# CREAR CHAT
# --------------------------------------------------

@app.post("/chats")
def create_new_chat(
    request: CreateChatRequest
):
    try:
        chat_data = create_chat(
            title=request.title
        )

        return chat_data

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# LISTAR CHATS
# --------------------------------------------------

@app.get("/chats")
def get_chats():
    try:
        return list_chats()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# OBTENER CHAT + MENSAJES
# --------------------------------------------------

@app.get("/chats/{chat_id}")
def get_chat_data(
    chat_id: int
):
    try:
        chat_data = get_chat(
            chat_id
        )

        if chat_data is None:
            raise HTTPException(
                status_code=404,
                detail="Chat no encontrado"
            )

        messages = get_chat_messages(
            chat_id
        )

        return {
            **chat_data,
            "messages": messages
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# CAMBIAR TÍTULO
# --------------------------------------------------

@app.patch("/chats/{chat_id}")
def rename_chat(
    chat_id: int,
    request: UpdateChatTitleRequest
):
    try:
        chat_data = update_chat_title(
            chat_id,
            request.title
        )

        if chat_data is None:
            raise HTTPException(
                status_code=404,
                detail="Chat no encontrado"
            )

        return chat_data

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# BORRAR CHAT
# --------------------------------------------------

@app.delete("/chats/{chat_id}")
def remove_chat(
    chat_id: int
):
    try:
        deleted = delete_chat(
            chat_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Chat no encontrado"
            )

        return {
            "deleted": True,
            "chat_id": chat_id
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# ENVIAR MENSAJE A UN CHAT
# --------------------------------------------------

@app.post(
    "/chats/{chat_id}/messages"
)
def send_chat_message(
    chat_id: int,
    request: SendMessageRequest
):
    try:
        # ------------------------------------------
        # Verificar chat
        # ------------------------------------------

        chat_data = get_chat(
            chat_id
        )

        if chat_data is None:
            raise HTTPException(
                status_code=404,
                detail="Chat no encontrado"
            )

        user_message = (
            request.message.strip()
        )

        # ------------------------------------------
        # Obtener historial ANTES de guardar
        # el mensaje actual.
        #
        # generate_response() agrega el mensaje
        # actual por su cuenta.
        # ------------------------------------------

        history = get_chat_history(
            chat_id,
            limit=20
        )

        # ------------------------------------------
        # Guardar mensaje del usuario
        # ------------------------------------------

        saved_user_message = save_message(
            chat_id=chat_id,
            role="user",
            content=user_message,
            sources=[]
        )

        # ------------------------------------------
        # Generar título con primer mensaje
        # ------------------------------------------

        # ------------------------------------------
        # Actualizar título dinámicamente
        # ------------------------------------------

        user_messages = [
            message["content"]
            for message in history
            if message["role"] == "user"
        ]

        # Agregar el mensaje actual
        user_messages.append(
            user_message
        )

        meaningful_messages = [
            message
            for message in user_messages
            if is_meaningful_for_title(message)
        ]

        # Títulos genéricos que siempre permitimos reemplazar.
        generic_titles = {
            "Nuevo chat",
            "Conversación con Jarvis",
        }

        # Actualizar el título:
        # - inmediatamente si todavía es genérico
        # - después cada 2 mensajes relevantes
        should_update_title = (
            len(meaningful_messages) > 0
            and (
                chat_data["title"] in generic_titles
                or len(meaningful_messages) % 2 == 0
            )
        )

        if should_update_title:

            # Usamos varios mensajes recientes para que
            # Qwen entienda el tema real del chat.
            title_context = "\n".join(
                meaningful_messages[-6:]
            )

            new_title = generate_chat_title(
                title_context
            )

            if (
                new_title
                and new_title != "Nuevo chat"
                and new_title != "Conversación con Jarvis"
                and new_title != chat_data["title"]
            ):
                update_chat_title(
                    chat_id,
                    new_title
                )

                print(
                    f"Título actualizado: "
                    f"{chat_data['title']} -> {new_title}"
                )

        # ------------------------------------------
        # Generar respuesta
        # ------------------------------------------

        response = generate_response(
            user_message=user_message,
            history=history
        )

        # ------------------------------------------
        # Guardar respuesta de Jarvis
        # ------------------------------------------

        saved_assistant_message = (
            save_message(
                chat_id=chat_id,
                role="assistant",
                content=response["answer"],
                sources=response["sources"]
            )
        )

        # ------------------------------------------
        # Respuesta al frontend
        # ------------------------------------------

        return {
            "chat_id": chat_id,

            "user_message":
                saved_user_message,

            "assistant_message":
                saved_assistant_message,

            "model":
                response["model"]
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            f"Error en chat {chat_id}: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# BUSCAR CONOCIMIENTO
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