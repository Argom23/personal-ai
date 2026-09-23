from pathlib import Path
import json
import re

import numpy as np
import requests

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b" # lOW qwen3.5:9b / HI qwen3.5:27b

STYLE_FILE = Path(
    "data/processed/style_prompt.txt"
)

EXAMPLES_FILE = Path(
    "data/processed/style_examples_clean.jsonl"
)

EMBEDDINGS_FILE = Path(
    "data/processed/style_embeddings.npy"
)

KNOWLEDGE_CHUNKS_FILE = Path(
    "data/processed/knowledge_chunks.jsonl"
)

KNOWLEDGE_EMBEDDINGS_FILE = Path(
    "data/processed/knowledge_embeddings.npy"
)

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# --------------------------------------------------
# MODELO DE EMBEDDINGS
# --------------------------------------------------

print("Cargando modelo de embeddings...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)


# --------------------------------------------------
# PERFIL DE ESTILO
# --------------------------------------------------

def load_style():

    if not STYLE_FILE.exists():
        return ""

    return STYLE_FILE.read_text(
        encoding="utf-8"
    )


# --------------------------------------------------
# EJEMPLOS DE PERSONALIDAD
# --------------------------------------------------

def load_examples():

    examples = []

    if not EXAMPLES_FILE.exists():
        return examples

    with open(
        EXAMPLES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:
            examples.append(
                json.loads(line)
            )

    return examples


print("Cargando ejemplos...")

examples = load_examples()

print(
    f"Ejemplos disponibles: {len(examples)}"
)

contexts = [
    example["context"]
    for example in examples
]


# --------------------------------------------------
# EMBEDDINGS DE PERSONALIDAD
# --------------------------------------------------

print("Cargando embeddings de personalidad...")

embeddings = np.load(
    EMBEDDINGS_FILE
)

print(
    f"Embeddings cargados: {embeddings.shape}"
)


# --------------------------------------------------
# CONOCIMIENTO / RAG
# --------------------------------------------------

def load_knowledge_chunks():

    chunks = []

    if not KNOWLEDGE_CHUNKS_FILE.exists():
        return chunks

    with open(
        KNOWLEDGE_CHUNKS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:
            chunks.append(
                json.loads(line)
            )

    return chunks


print("Cargando biblioteca académica...")

knowledge_chunks = load_knowledge_chunks()


if KNOWLEDGE_EMBEDDINGS_FILE.exists():

    knowledge_embeddings = np.load(
        KNOWLEDGE_EMBEDDINGS_FILE
    )

else:

    knowledge_embeddings = None


print(
    f"Fragmentos académicos: "
    f"{len(knowledge_chunks)}"
)


# --------------------------------------------------
# BÚSQUEDA ACADÉMICA
# --------------------------------------------------

def search_knowledge(query, n=5):

    if (
        knowledge_embeddings is None
        or not knowledge_chunks
    ):
        return []

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )[0]

    similarities = (
        knowledge_embeddings
        @ query_embedding
    )

    best_indices = np.argsort(
        similarities
    )[::-1][:n]

    results = []

    for index in best_indices:

        chunk = knowledge_chunks[index]

        results.append(
            {
                "source": chunk["source"],
                "page": chunk["page"],
                "text": chunk["text"],
                "similarity": float(
                    similarities[index]
                )
            }
        )

    return results


def format_knowledge(results):

    if not results:
        return (
            "No se encontraron fuentes "
            "académicas relevantes."
        )

    parts = []

    for result in results:

        parts.append(
            f"""
FUENTE:
{result["source"]}

PÁGINA PDF:
{result["page"]}

CONTENIDO:
{result["text"]}
""".strip()
        )

    return "\n\n".join(parts)


# --------------------------------------------------
# TF-IDF PARA PERSONALIDAD
# --------------------------------------------------

print("Construyendo índice TF-IDF...")

tfidf_vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    max_df=0.95,
    min_df=2
)

tfidf_matrix = tfidf_vectorizer.fit_transform(
    contexts
)

print(
    f"TF-IDF listo: {tfidf_matrix.shape}"
)


# --------------------------------------------------
# FILTROS
# --------------------------------------------------

URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE
)


def valid_example(example):

    context = example["context"].strip()
    response = example["response"].strip()

    if not context or not response:
        return False

    if URL_PATTERN.search(response):
        return False

    return True


# --------------------------------------------------
# BÚSQUEDA DE EJEMPLOS DE PERSONALIDAD
# --------------------------------------------------

def search_examples(user_message, n=8):

    # Búsqueda semántica
    query_embedding = embedding_model.encode(
        [user_message],
        normalize_embeddings=True
    )[0]

    semantic_scores = (
        embeddings @ query_embedding
    )

    # Búsqueda léxica
    query_tfidf = tfidf_vectorizer.transform(
        [user_message]
    )

    lexical_scores = cosine_similarity(
        query_tfidf,
        tfidf_matrix
    )[0]

    # Score híbrido
    final_scores = (
        0.55 * semantic_scores
        +
        0.45 * lexical_scores
    )

    candidate_indices = np.argsort(
        final_scores
    )[::-1][:n * 5]

    results = []
    seen_responses = set()

    for index in candidate_indices:

        example = examples[index]

        if not valid_example(example):
            continue

        response_normalized = (
            example["response"]
            .strip()
            .lower()
        )

        if response_normalized in seen_responses:
            continue

        seen_responses.add(
            response_normalized
        )

        results.append(
            {
                "context":
                    example["context"],

                "response":
                    example["response"],

                "score":
                    float(
                        final_scores[index]
                    ),

                "semantic":
                    float(
                        semantic_scores[index]
                    ),

                "lexical":
                    float(
                        lexical_scores[index]
                    ),
            }
        )

        if len(results) >= n:
            break

    return results


# --------------------------------------------------
# FORMATO DE EJEMPLOS
# --------------------------------------------------

def format_examples(results):

    parts = []

    for example in results:

        parts.append(
            f"""
Mensaje recibido:
{example["context"]}

Respuesta real del usuario:
{example["response"]}
""".strip()
        )

    return "\n\n".join(parts)


# --------------------------------------------------
# GENERACIÓN
# --------------------------------------------------

def generate_response(
    user_message,
    history
):

    style = load_style()

    # -------------------------
    # Personalidad
    # -------------------------

    relevant_examples = search_examples(
        user_message,
        n=10
    )

    examples_text = format_examples(
        relevant_examples
    )

    # -------------------------
    # Conocimiento académico
    # -------------------------

    knowledge_results = search_knowledge(
        user_message,
        n=5
    )

    knowledge_text = format_knowledge(
        knowledge_results
    )

    # -------------------------
    # Prompt del sistema
    # -------------------------

    system_prompt = f"""
Respondé como una persona conversando por chat.

No actúes como chatbot, asistente virtual ni servicio de atención.

Tu forma de escribir debe inspirarse en el estilo real del usuario.

PERFIL DE ESTILO:

{style}


EJEMPLOS REALES DE CÓMO RESPONDE EL USUARIO:

{examples_text}


MATERIAL ACADÉMICO RECUPERADO:

{knowledge_text}


REGLAS DE ESTILO:

- Respondé directamente.
- No digás "¿En qué puedo ayudarte?".
- No digás "¿Te gustaría saber más?".
- No digás "Como asistente".
- No conviertas cada respuesta en una pregunta.
- No uses emojis porque sí.
- No exageres palabras como mae, bro, di o JAJA.
- Si la respuesta natural es corta, mantenela corta.
- Usá los ejemplos como referencia de tono y longitud.
- No copies literalmente los ejemplos.
- No repitas innecesariamente lo que acaba de decir el usuario.
- Recordá el contexto de la conversación actual.


REGLAS PARA FUENTES ACADÉMICAS:

- Cuando el material recuperado sea relevante,
  utilizalo como fuente principal.
- No inventes contenido que no aparece en las fuentes.
- Indicá el nombre del PDF y la página PDF cuando uses información
  recuperada del libro.
- Si el material recuperado no responde realmente la pregunta,
  no finjas que sí.
- Podés combinar las fuentes con razonamiento matemático propio.


SI HABLAN DE FÍSICA, MATEMÁTICA O CIENCIA:

- Priorizá la exactitud.
- Explicá más cuando haga falta.
- No inventés datos.
- Si no estás seguro de algo, decilo.
- Mostrá fórmulas claramente.
- Podés responder más largo que el estilo habitual si el tema lo requiere.
""".strip()

    # --------------------------------------------------
    # HISTORIAL
    # --------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for turn in history[-8:]:

        messages.append(
            {
                "role": turn["role"],
                "content": turn["content"]
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # --------------------------------------------------
    # OLLAMA
    # --------------------------------------------------

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,

            "messages": messages,

            "stream": False,

            "think": False,

            "options": {
                "temperature": 0.5,
                "top_p": 0.85
            }
        },
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return (
        data["message"]["content"]
        .strip()
    )


# --------------------------------------------------
# DEBUG PERSONALIDAD
# --------------------------------------------------

def debug_examples(
    user_message
):

    results = search_examples(
        user_message,
        n=8
    )

    print(
        "\n=== EJEMPLOS ENCONTRADOS ==="
    )

    for result in results:

        print(
            f"\nScore: "
            f"{result['score']:.3f}"
        )

        print(
            f"Semántica: "
            f"{result['semantic']:.3f}"
        )

        print(
            f"Léxica: "
            f"{result['lexical']:.3f}"
        )

        print(
            f"Contexto: "
            f"{result['context']}"
        )

        print(
            f"Respuesta: "
            f"{result['response']}"
        )


# --------------------------------------------------
# DEBUG LIBROS / PAPERS
# --------------------------------------------------

def debug_knowledge(
    query
):

    results = search_knowledge(
        query,
        n=5
    )

    print(
        "\n=== FUENTES ENCONTRADAS ==="
    )

    if not results:

        print(
            "\nNo se encontraron fuentes."
        )

        return

    for result in results:

        print()
        print(
            f"Similitud: "
            f"{result['similarity']:.3f}"
        )

        print(
            f"Fuente: "
            f"{result['source']}"
        )

        print(
            f"Página PDF: "
            f"{result['page']}"
        )

        print(
            "\nFragmento:"
        )

        print(
            result["text"][:700]
        )

        print(
            "\n--------------------------"
        )


# --------------------------------------------------
# CHAT
# --------------------------------------------------

if __name__ == "__main__":

    history = []

    while True:

        try:

            message = input(
                "\nVos: "
            ).strip()

        except KeyboardInterrupt:

            print(
                "\nSaliendo..."
            )

            break

        if not message:
            continue

        if message.lower() in {
            "exit",
            "quit",
            "salir"
        }:
            break

        # -------------------------
        # Debug personalidad
        # -------------------------

        if message.startswith(
            "/examples "
        ):

            query = message[
                len("/examples "):
            ]

            debug_examples(
                query
            )

            continue

        # -------------------------
        # Debug RAG
        # -------------------------

        if message.startswith(
            "/book "
        ):

            query = message[
                len("/book "):
            ]

            debug_knowledge(
                query
            )

            continue

        # -------------------------
        # Generar respuesta
        # -------------------------

        try:

            answer = generate_response(
                message,
                history
            )

        except requests.exceptions.RequestException as error:

            print(
                "\nError comunicándose con Ollama:"
            )

            print(error)

            continue

        print(
            "\nIA:"
        )

        print(
            answer
        )

        history.append(
            {
                "role": "user",
                "content": message
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )