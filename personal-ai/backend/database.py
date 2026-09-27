from pathlib import Path
import json
import sqlite3


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"

DATABASE_FILE = DATA_DIR / "jarvis.db"


# --------------------------------------------------
# CONEXIÓN
# --------------------------------------------------

def get_connection():
    """
    Abre una conexión nueva a SQLite.

    Cada operación usa su propia conexión para evitar
    problemas cuando FastAPI atiende varias solicitudes.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    # Las relaciones con claves foráneas no vienen
    # activadas por defecto en SQLite.
    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return connection


# --------------------------------------------------
# CREAR BASE DE DATOS
# --------------------------------------------------

def init_database():
    """
    Crea las tablas necesarias si todavía no existen.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ------------------------------------------
        # CHATS
        # ------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                title TEXT NOT NULL DEFAULT 'Nuevo chat',

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # ------------------------------------------
        # MENSAJES
        # ------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                role TEXT NOT NULL
                    CHECK(role IN ('user', 'assistant')),

                content TEXT NOT NULL,

                sources_json TEXT,

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            );
            """
        )

        # Índice para recuperar rápidamente los
        # mensajes de una conversación.
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_messages_chat_id
            ON messages(chat_id);
            """
        )

        connection.commit()

    finally:
        connection.close()


# --------------------------------------------------
# CREAR CHAT
# --------------------------------------------------

def create_chat(
    title: str = "Nuevo chat"
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO chats (title)
            VALUES (?);
            """,
            (title,)
        )

        chat_id = cursor.lastrowid

        connection.commit()

        return get_chat(chat_id)

    finally:
        connection.close()


# --------------------------------------------------
# OBTENER CHAT
# --------------------------------------------------

def get_chat(chat_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                created_at,
                updated_at
            FROM chats
            WHERE id = ?;
            """,
            (chat_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


# --------------------------------------------------
# LISTAR CHATS
# --------------------------------------------------

def list_chats():
    """
    Devuelve los chats más recientemente usados primero.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                created_at,
                updated_at
            FROM chats
            ORDER BY updated_at DESC, id DESC;
            """
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


# --------------------------------------------------
# CAMBIAR TÍTULO
# --------------------------------------------------

def update_chat_title(
    chat_id: int,
    title: str
):
    title = title.strip()

    if not title:
        title = "Nuevo chat"

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE chats
            SET
                title = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (
                title,
                chat_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            return None

        return get_chat(chat_id)

    finally:
        connection.close()


# --------------------------------------------------
# BORRAR CHAT
# --------------------------------------------------

def delete_chat(chat_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM chats
            WHERE id = ?;
            """,
            (chat_id,)
        )

        deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    finally:
        connection.close()


# --------------------------------------------------
# GUARDAR MENSAJE
# --------------------------------------------------

def save_message(
    chat_id: int,
    role: str,
    content: str,
    sources=None
):
    if role not in {
        "user",
        "assistant"
    }:
        raise ValueError(
            "role debe ser 'user' o 'assistant'"
        )

    if sources is None:
        sources = []

    sources_json = json.dumps(
        sources,
        ensure_ascii=False
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Confirmar que el chat existe.
        cursor.execute(
            """
            SELECT id
            FROM chats
            WHERE id = ?;
            """,
            (chat_id,)
        )

        if cursor.fetchone() is None:
            return None

        cursor.execute(
            """
            INSERT INTO messages (
                chat_id,
                role,
                content,
                sources_json
            )
            VALUES (?, ?, ?, ?);
            """,
            (
                chat_id,
                role,
                content,
                sources_json
            )
        )

        message_id = cursor.lastrowid

        # Cada mensaje actualiza la fecha del chat.
        cursor.execute(
            """
            UPDATE chats
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (chat_id,)
        )

        connection.commit()

        return get_message(message_id)

    finally:
        connection.close()


# --------------------------------------------------
# OBTENER UN MENSAJE
# --------------------------------------------------

def get_message(message_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                sources_json,
                created_at
            FROM messages
            WHERE id = ?;
            """,
            (message_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        message = dict(row)

        try:
            message["sources"] = json.loads(
                message["sources_json"] or "[]"
            )

        except json.JSONDecodeError:
            message["sources"] = []

        del message["sources_json"]

        return message

    finally:
        connection.close()


# --------------------------------------------------
# OBTENER MENSAJES DE UN CHAT
# --------------------------------------------------

def get_chat_messages(chat_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                sources_json,
                created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC;
            """,
            (chat_id,)
        )

        rows = cursor.fetchall()

        messages = []

        for row in rows:
            message = dict(row)

            try:
                message["sources"] = json.loads(
                    message["sources_json"] or "[]"
                )

            except json.JSONDecodeError:
                message["sources"] = []

            del message["sources_json"]

            messages.append(
                message
            )

        return messages

    finally:
        connection.close()


# --------------------------------------------------
# HISTORIAL PARA EL MODELO
# --------------------------------------------------

def get_chat_history(
    chat_id: int,
    limit: int = 20
):
    """
    Devuelve solamente role + content.

    Esto es lo que después enviaremos a
    generate_response().
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                role,
                content
            FROM (
                SELECT
                    id,
                    role,
                    content
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC;
            """,
            (
                chat_id,
                limit
            )
        )

        rows = cursor.fetchall()

        return [
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in rows
        ]

    finally:
        connection.close()


# --------------------------------------------------
# GENERAR TÍTULO SIMPLE
# --------------------------------------------------

def generate_title_from_message(
    message: str,
    max_length: int = 45
):
    text = " ".join(
        message.strip().split()
    )

    if not text:
        return "Nuevo chat"

    lower = text.lower()

    # Saludos simples
    casual = {
        "hola",
        "holaa",
        "buenas",
        "hey",
        "hola jarvis",
    }

    if lower in casual:
        return "Conversación con Jarvis"

    # Preguntas frecuentes
    replacements = [
        ("explicame ", ""),
        ("explícame ", ""),
        ("que es ", ""),
        ("qué es ", ""),
        ("como funciona ", ""),
        ("cómo funciona ", ""),
        ("ayudame con ", ""),
        ("ayúdame con ", ""),
        ("quiero saber ", ""),
        ("una consulta, ", ""),
        ("una consulta ", ""),
    ]

    title = lower

    for prefix, replacement in replacements:
        if title.startswith(prefix):
            title = title.replace(
                prefix,
                replacement,
                1
            )
            break

    title = title.strip(
        " ¿?¡!.,:"
    )

    if not title:
        return "Nuevo chat"

    # Capitalizar solo la primera letra
    title = (
        title[0].upper()
        + title[1:]
    )

    if len(title) > max_length:
        title = (
            title[:max_length]
            .rstrip()
            + "..."
        )

    return title


# --------------------------------------------------
# INICIALIZACIÓN
# --------------------------------------------------

init_database()

print(
    f"Base de datos lista: {DATABASE_FILE}"
)