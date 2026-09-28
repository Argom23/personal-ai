from pathlib import Path
import json
import re
import unicodedata

import numpy as np
import requests

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# RUTAS DEL PROYECTO
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL = "qwen3.5:9b"


STYLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "style_prompt.txt"
)

EXAMPLES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "style_examples_clean.jsonl"
)

EMBEDDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "style_embeddings.npy"
)

KNOWLEDGE_CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_chunks.jsonl"
)

KNOWLEDGE_EMBEDDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_embeddings.npy"
)

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

FORBIDDEN_STYLE_TERMS = [
    "amor",
    "mi amor",
    "bebé",
    "bebe",
    "bb",
    "mi vida",
    "corazón",
    "corazon",
    "cariño",
    "cariño mío",
    "precioso",
    "guapo",
]
# ------------------------------------------------------------------
# HACER QUE DEJE DE DECIR PALABRAS
# ------------------------------------------------------------------

def is_safe_style_example(text: str) -> bool:
    lowered = text.lower()

    return not any(
        term in lowered
        for term in FORBIDDEN_STYLE_TERMS
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

def should_use_rag(message: str) -> bool:
    text = message.lower().strip()

    casual_messages = {
        "hola",
        "holaa",
        "buenas",
        "hey",
        "gracias",
        "muchas gracias",
        "ok",
        "okay",
        "dale",
        "listo",
        "jaja",
        "jajaja",
        "xd",
        "hmm ok",
    }

    if text in casual_messages:
        return False

    academic_terms = [
        "explica",
        "explícame",
        "explicame",
        "demuestra",
        "demostrar",
        "ecuación",
        "ecuacion",
        "teorema",
        "derivada",
        "integral",
        "física",
        "fisica",
        "matemática",
        "matematica",
        "química",
        "quimica",
        "cauchy",
        "riemann",
        "función",
        "funcion",
        "armónica",
        "armonica",
        "mecánica",
        "mecanica",
        "ondas",
        "óptica",
        "optica",
        "libro",
        "paper",
        "fuente",
        "fuentes",
        "según",
        "segun",
        "página",
        "pagina",
    ]

    return any(
        term in text
        for term in academic_terms
    )

# --------------------------------------------------
# TF-IDF PARA CONOCIMIENTO
# --------------------------------------------------

print("Construyendo índice TF-IDF académico...")

knowledge_texts = [
    chunk["text"]
    for chunk in knowledge_chunks
]

knowledge_tfidf_vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    max_df=0.98,
    min_df=1
)

if knowledge_texts:

    knowledge_tfidf_matrix = (
        knowledge_tfidf_vectorizer.fit_transform(
            knowledge_texts
        )
    )

    print(
        f"TF-IDF académico listo: "
        f"{knowledge_tfidf_matrix.shape}"
    )

else:

    knowledge_tfidf_matrix = None

    print(
        "No hay documentos académicos indexados."
    )


# --------------------------------------------------
# BÚSQUEDA ACADÉMICA
# --------------------------------------------------

def normalize_source_name(text: str) -> str:
    """
    Normaliza nombres de PDFs y texto del usuario para poder comparar
    cosas como:
        Brown-Churchill.pdf -> brown churchill
        Mecánica clásica    -> mecanica clasica
    """
    text = text.lower().strip()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    )

    return " ".join(
        text.split()
    )


def detect_source_filter(message: str):
    """
    Detecta automáticamente una o varias fuentes mencionadas por el usuario
    cuando pide exclusividad, por ejemplo:

        "usa solo Brown-Churchill"
        "basate solo en Halliday"
        "usa únicamente Boas"
        "usa solo Brown-Churchill y Boas"

    Retorna:
        None -> no se pidió limitar fuentes
        []   -> se pidió una fuente exclusiva, pero no se reconoció
        [...] -> nombres exactos de los PDFs encontrados
    """
    text = normalize_source_name(
        message
    )

    exclusive_markers = [
        "solo",
        "solamente",
        "unicamente",
        "exclusivamente",
        "usa solo",
        "use solo",
        "basate solo",
        "basate unicamente",
    ]

    wants_exclusive_source = any(
        normalize_source_name(marker) in text
        for marker in exclusive_markers
    )

    if not wants_exclusive_source:
        return None

    sources = sorted({
        chunk["source"]
        for chunk in knowledge_chunks
    })

    if not sources:
        return []

    query_tokens = set(
        text.split()
    )

    stopwords = {
        "pdf",
        "the",
        "and",
        "of",
        "in",
        "by",
        "a",
        "an",
        "de",
        "del",
        "la",
        "el",
        "los",
        "las",
        "y",
        "vol",
        "volume",
        "edition",
        "ed",
    }

    source_tokens = {}
    token_frequency = {}

    for source in sources:
        stem = Path(source).stem
        normalized = normalize_source_name(
            stem
        )

        tokens = {
            token
            for token in normalized.split()
            if len(token) >= 3
            and token not in stopwords
        }

        source_tokens[source] = (
            normalized,
            tokens
        )

        for token in tokens:
            token_frequency[token] = (
                token_frequency.get(token, 0)
                + 1
            )

    scored_matches = []

    for source in sources:
        normalized, tokens = (
            source_tokens[source]
        )

        # Si el usuario escribió prácticamente el nombre completo del PDF.
        if (
            normalized
            and normalized in text
        ):
            scored_matches.append(
                (1000 + len(tokens), source)
            )
            continue

        overlap = (
            tokens
            & query_tokens
        )

        if not overlap:
            continue

        distinctive_overlap = {
            token
            for token in overlap
            if token_frequency.get(token, 0) == 1
        }

        # Un apellido/nombre distintivo basta:
        # Brown, Churchill, Halliday, Resnick, Boas, etc.
        if distinctive_overlap:
            score = (
                10 * len(distinctive_overlap)
                + len(overlap)
            )

            scored_matches.append(
                (score, source)
            )
            continue

        # Si no hay token único, exigimos al menos dos coincidencias.
        if len(overlap) >= 2:
            scored_matches.append(
                (len(overlap), source)
            )

    if not scored_matches:
        return []

    # Permitimos varias fuentes si el usuario menciona varias explícitamente.
    scored_matches.sort(
        reverse=True
    )

    best_score = scored_matches[0][0]

    selected_sources = [
        source
        for score, source in scored_matches
        if score >= max(
            2,
            best_score - 2
        )
    ]

    return selected_sources


def search_knowledge(query, n=5, source_filter=None):

    if (
        knowledge_embeddings is None
        or not knowledge_chunks
        or knowledge_tfidf_matrix is None
    ):
        return []

    # Similitud semántica
    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )[0]

    semantic_scores = (
        knowledge_embeddings
        @ query_embedding
    )

    # Similitud léxica
    query_tfidf = (
        knowledge_tfidf_vectorizer.transform(
            [query]
        )
    )

    lexical_scores = cosine_similarity(
        query_tfidf,
        knowledge_tfidf_matrix
    )[0]

    # Score híbrido: significado + coincidencia de términos
    final_scores = (
        0.70 * semantic_scores
        +
        0.30 * lexical_scores
    )

    # Tomamos más candidatos para poder diversificar por PDF.
    candidate_indices = np.argsort(
        final_scores
    )[::-1][:n * 30]

    results = []
    source_counts = {}

    for index in candidate_indices:

        chunk = knowledge_chunks[index]
        source = chunk["source"]

        # Si el usuario pidió una o varias fuentes específicas,
        # solo aceptamos esos PDFs exactos.
        if source_filter is not None:
            if source not in source_filter:
                continue

        count = source_counts.get(
            source,
            0
        )

        # Máximo dos fragmentos del mismo PDF.
        if count >= 2:
            continue

        source_counts[source] = count + 1

        results.append(
            {
                "source": source,
                "page": chunk["page"],
                "text": chunk["text"],
                "similarity": float(
                    final_scores[index]
                ),
                "semantic": float(
                    semantic_scores[index]
                ),
                "lexical": float(
                    lexical_scores[index]
                )
            }
        )

        if len(results) >= n:
            break

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

    if not is_safe_style_example(response):
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

# -------------------------------------------------
# DETECT RESPONSE LANGUAGE
# -------------------------------------------------

def detect_response_mode(message: str) -> str:
    text = message.lower().strip()

    casual_patterns = [
        "hola",
        "holaa",
        "buenas",
        "gracias",
        "ok",
        "okay",
        "dale",
        "listo",
        "jaja",
        "jajaja",
        "xd",
    ]

    if text in casual_patterns:
        return "casual"

    explanation_patterns = [
        "explica",
        "explícame",
        "explicame",
        "por qué",
        "porque",
        "para qué",
        "para que",
        "qué significa",
        "que significa",
        "qué hace que",
        "que hace que",
        "cómo funciona",
        "como funciona",
        "qué es",
        "que es",
        "cuál es la relación",
        "cual es la relacion",
        "cómo se relaciona",
        "como se relaciona",
    ]

    if any(
        pattern in text
        for pattern in explanation_patterns
    ):
        return "explanation"

    problem_patterns = [
        "resuelve",
        "resolver",
        "calcula",
        "calcular",
        "demuestra",
        "demostrar",
        "encuentra",
        "hallar",
        "despeja",
        "ejercicio",
        "problema",
    ]

    if any(
        pattern in text
        for pattern in problem_patterns
    ):
        return "problem_solving"

    coding_patterns = [
        "código",
        "codigo",
        "programa",
        "programar",
        "python",
        "javascript",
        "typescript",
        "java",
        "fortran",
        "c++",
        "codigo en c",
        "código en c",
        "función en",
        "funcion en",
        "script",
    ]

    if any(
        pattern in text
        for pattern in coding_patterns
    ):
        return "coding"

    return "normal"


def response_mode_prompt(mode: str) -> str:

    if mode == "casual":
        return """
MODO DE RESPUESTA: CASUAL

- Respondé de forma breve y natural.
- No desarrolles explicaciones innecesarias.
- No conviertas un saludo o comentario simple en una respuesta larga.
""".strip()

    if mode == "explanation":
        return """
MODO DE RESPUESTA: EXPLICACIÓN

- El usuario está intentando entender un concepto.
- Desarrollá la respuesta lo suficiente para explicar realmente la idea.
- No respondas solamente con una definición corta.
- Explicá qué significa, cómo funciona y por qué es importante cuando corresponda.
- Cuando sea útil, empezá con una explicación intuitiva y luego pasá a la parte formal.
- Relacioná explícitamente los conceptos mencionados por el usuario.
- Usá ejemplos breves si ayudan a entender.
- En matemática y física, explicá tanto la interpretación como las ecuaciones.
- Priorizá comprensión y exactitud sobre imitar la brevedad del estilo del usuario.
""".strip()

    if mode == "problem_solving":
        return """
MODO DE RESPUESTA: RESOLUCIÓN DE PROBLEMAS

- Resolvé el problema de forma ordenada.
- Mostrá los pasos importantes.
- Explicá por qué se realiza cada paso cuando no sea obvio.
- No saltés directamente al resultado salvo que el usuario pida solo la respuesta.
- Para matemática y física, usá LaTeX correctamente.
- Verificá el resultado cuando sea posible.
""".strip()

    if mode == "coding":
        return """
MODO DE RESPUESTA: PROGRAMACIÓN

- Priorizá código correcto y claro.
- Usá bloques de código con el lenguaje correspondiente.
- Explicá las partes importantes del código.
- Si existe un error, explicá primero su causa y después la corrección.
- No agregues complejidad innecesaria.
""".strip()

    return """
MODO DE RESPUESTA: NORMAL

- Ajustá la longitud de la respuesta a la pregunta.
- Respondé directamente y con suficiente contexto.
""".strip()

# --------------------------------------------------
# GENERACIÓN
# --------------------------------------------------
def is_meaningful_for_title(
    message: str
) -> bool:
    text = message.lower().strip()

    if not text:
        return False

    casual_messages = {
        "hola",
        "holaa",
        "holaaa",
        "buenas",
        "hey",
        "gracias",
        "muchas gracias",
        "ok",
        "okay",
        "dale",
        "listo",
        "jaja",
        "jajaja",
        "xd",
        "hmm",
        "hmm ok",
        "como estas",
        "cómo estás",
        "todo bien",
        "que tal",
        "qué tal",
    }

    if text in casual_messages:
        return False

    # Mensajes demasiado cortos suelen no dar suficiente contexto.
    if len(text.split()) < 2:
        return False

    return True

def generate_chat_title(
    conversation_text: str
) -> str:
    """
    Genera un título corto que represente
    el tema actual de la conversación.
    """

    prompt = f"""
Generá un título corto para esta conversación.

CONVERSACIÓN:
{conversation_text}

REGLAS:

- Máximo 5 palabras.
- Resumí el tema principal actual.
- No respondas a la conversación.
- No expliques nada.
- No uses comillas.
- No pongas punto al final.
- No uses emojis.
- No escribas "Título:".
- Conservá nombres técnicos importantes como Cauchy-Riemann,
  hydro.f90, Fortran, Python, Schrödinger, etc.
- Si todavía no existe un tema claro, respondé exactamente:
  Nuevo chat

Respondé únicamente con el título.
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content":
                            "Generás títulos breves y descriptivos."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8
                }
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        title = (
            data["message"]["content"]
            .strip()
            .strip('"')
            .strip("'")
        )

        if not title:
            return "Nuevo chat"

        if len(title) > 60:
            title = (
                title[:60].rstrip()
                + "..."
            )

        return title

    except Exception as error:
        print(
            f"Error generando título: {error}"
        )

        return "Nuevo chat"

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

    source_filter = detect_source_filter(
        user_message
    )

    if source_filter is not None:
        print(
            f"Filtro de fuentes solicitado: {source_filter}"
        )

    if should_use_rag(user_message):
        knowledge_results = search_knowledge(
            user_message,
            n=4,
            source_filter=source_filter
        )
    else:
        knowledge_results = []

    knowledge_text = format_knowledge(
        knowledge_results
    )

    response_mode = detect_response_mode(
    user_message
    )

    mode_instructions = response_mode_prompt(
        response_mode
    )

    # -------------------------
    # Prompt del sistema
    # -------------------------

    system_prompt = f"""
Tu nombre es Jarvis.

Sos un asistente personal local que conversa con el usuario de forma natural.
Respondé como una persona conversando por chat, sin sonar como un chatbot,
servicio de atención al cliente ni respuesta corporativa.

MODO ACTUAL DE RESPUESTA:

{mode_instructions}

Las instrucciones del modo actual tienen prioridad sobre las preferencias
generales de longitud y nivel de detalle.

IDENTIDAD:

- Tu nombre es Jarvis.
- Si el usuario pregunta cómo te llamás, respondé que te llamás Jarvis.
- No digás que tu nombre es "modelo", "Qwen" ni algo similar.
- No inventés capacidades que la aplicación no tenga.
- Recordá el contexto de la conversación actual.


ESTILO DEL USUARIO:

Tu forma de escribir debe inspirarse en el estilo real del usuario.

PERFIL DE ESTILO:

{style}


EJEMPLOS REALES DE CÓMO RESPONDE EL USUARIO:

{examples_text}


IMPORTANTE SOBRE LOS EJEMPLOS:

- Los ejemplos anteriores fueron escritos por el usuario.
- Usalos únicamente para aprender su tono, vocabulario, ritmo,
  informalidad y longitud habitual de las respuestas.
- No copies literalmente los ejemplos.
- No copies información factual de los ejemplos como si fuera conocimiento.
- No asumas que las relaciones personales presentes en los chats originales
  también existen en esta conversación.
- No imites comportamientos románticos, afectivos o de pareja que aparezcan
  en los chats usados como ejemplos.
- Nunca llames al usuario "amor", "mi amor", "bebé", "bebe", "bb",
  "mi vida", "corazón", "corazon", "cariño", "cariño mío",
  "precioso" ni "guapo".
- No uses otros términos románticos o de pareja para dirigirte al usuario.


MATERIAL ACADÉMICO RECUPERADO:

{knowledge_text}


REGLAS GENERALES DE RESPUESTA:

- Respondé directamente a lo que preguntó el usuario.
- No digás "¿En qué puedo ayudarte?".
- No cierres respuestas con preguntas de seguimiento innecesarias.
- No digás "Como asistente".
- No conviertas cada respuesta en una pregunta.
- No uses emojis porque sí.
- No exageres palabras como "mae", "bro", "di" o "JAJA".
- Podés usar lenguaje informal cuando encaje naturalmente con el contexto.
- Para saludos, confirmaciones o mensajes casuales, podés responder corto.
- Cuando el usuario haga una pregunta conceptual, técnica, académica o pida
  una explicación, desarrollá la respuesta lo suficiente para que pueda
  entender el porqué, no solo memorizar una definición.
- No sacrifiques contenido importante por imitar la brevedad de los ejemplos
  de estilo.
- En preguntas de estudio, priorizá una explicación clara y completa aunque
  sea más larga que la forma habitual de escribir del usuario.
- Cuando sea útil, explicá primero la idea intuitiva y después la parte formal.
- Incluí relaciones, consecuencias o ejemplos breves cuando ayuden a entender.
- No repitas innecesariamente lo que acaba de decir el usuario.
- Priorizá que la respuesta sea útil y correcta antes que imitar perfectamente
  el estilo del usuario.
- No imites errores ortográficos solo porque aparezcan en los ejemplos.
- Si no sabés algo o no tenés suficiente información, decilo claramente.


REGLAS PARA FUENTES ACADÉMICAS:

- El material académico recuperado puede o no ser relevante para la pregunta.
- No uses una fuente únicamente porque fue recuperada.
- Cuando el material recuperado sea relevante, utilizalo como fuente principal.
- No atribuyas a una fuente información que no aparece en el fragmento recuperado.
- No inventes citas, páginas, autores ni contenido.
- Cuando uses información recuperada, indicá correctamente el PDF y la página PDF.
- Si el material recuperado no responde realmente la pregunta, no finjas que sí.
- Podés combinar las fuentes con razonamiento matemático o científico propio,
  dejando clara la diferencia cuando sea importante.
- Si el usuario pide utilizar una fuente específica, priorizá esa fuente.
- Si el usuario dice "usa solo", "basate solo" o equivalente respecto a una
  fuente determinada, no utilices otras fuentes para construir la respuesta.
- No menciones fuentes académicas en conversaciones casuales si no son necesarias.


FÍSICA, MATEMÁTICA, CIENCIA Y TEMAS TÉCNICOS:

- Priorizá la exactitud sobre el estilo.
- Explicá los pasos cuando sean importantes para entender el resultado.
- No inventés datos, fórmulas, definiciones ni resultados.
- Si no estás seguro de algo, decilo.
- Diferenciá entre lo que proviene de una fuente y lo que se deduce mediante
  razonamiento propio cuando sea relevante.
- Mostrá las fórmulas claramente.
- Escribí las expresiones matemáticas usando LaTeX.
- Para matemática dentro de una oración usá $...$.
- Para ecuaciones importantes o separadas usá $$...$$.
- No escribás fórmulas ambiguas en texto plano si pueden expresarse en LaTeX.
- No pongás fórmulas dentro de bloques de código.
- Para código de programación sí utilizá bloques de código con el lenguaje
  correspondiente.
- Podés responder más largo que el estilo habitual si el tema lo requiere.
- No respondas únicamente con una definición si la pregunta busca comprender
  un concepto.
- Explicá qué significa, por qué funciona o por qué es importante cuando eso
  sea relevante.
- Si existe una relación entre varios conceptos mencionados por el usuario,
  conectalos explícitamente.
- Cuando el tema sea matemático, explicá tanto la interpretación como las
  ecuaciones necesarias.
- Si el usuario pregunta "por qué", "cómo", "para qué" o "qué hace que",
  tratá la pregunta como una solicitud de explicación desarrollada.


COMPORTAMIENTO EN CONVERSACIÓN:

- Usá el historial para entender referencias como "eso", "el anterior",
  "ese libro" o "seguí con lo mismo".
- No afirmes recordar conversaciones anteriores si no aparecen en el historial
  o no fueron proporcionadas por la aplicación.
- No inventes cómo funciona la aplicación Jarvis.
- Si el usuario pregunta sobre una función de la aplicación que no conocés,
  indicá que no tenés suficiente información sobre esa función.
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

    answer = (
        data["message"]["content"]
        .strip()
    )

    sources = []

    for result in knowledge_results:
        sources.append(
            {
                "source": result["source"],
                "page": result["page"],
                "similarity": result["similarity"]
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "model": MODEL
    }


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
        n=5,
        source_filter=None
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
            f"Score híbrido: "
            f"{result['similarity']:.3f}"
        )

        print(
            f"Semántica: "
            f"{result.get('semantic', 0.0):.3f}"
        )

        print(
            f"Léxica: "
            f"{result.get('lexical', 0.0):.3f}"
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

# if __name__ == "__main__":

#     history = []

#     while True:

#         try:

#             message = input(
#                 "\nVos: "
#             ).strip()

#         except KeyboardInterrupt:

#             print(
#                 "\nSaliendo..."
#             )

#             break

#         if not message:
#             continue

#         if message.lower() in {
#             "exit",
#             "quit",
#             "salir"
#         }:
#             break

#         # -------------------------
#         # Debug personalidad
#         # -------------------------

#         if message.startswith(
#             "/examples "
#         ):

#             query = message[
#                 len("/examples "):
#             ]

#             debug_examples(
#                 query
#             )

#             continue

#         # -------------------------
#         # Debug RAG
#         # -------------------------

#         if message.startswith(
#             "/book "
#         ):

#             query = message[
#                 len("/book "):
#             ]

#             debug_knowledge(
#                 query
#             )

#             continue

#         # -------------------------
#         # Generar respuesta
#         # -------------------------

#         try:

#             answer = generate_response(
#                 message,
#                 history
#             )

#         except requests.exceptions.RequestException as error:

#             print(
#                 "\nError comunicándose con Ollama:"
#             )

#             print(error)

#             continue

#         print(
#             "\nIA:"
#         )

#         print(
#             answer
#         )

#         history.append(
#             {
#                 "role": "user",
#                 "content": message
#             }
#         )

#         history.append(
#             {
#                 "role": "assistant",
#                 "content": answer
#             }
#         )