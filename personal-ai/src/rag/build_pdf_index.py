from pathlib import Path
import json
import re

import fitz
import numpy as np
from sentence_transformers import SentenceTransformer


PDF_DIR = Path("data/papers")

CHUNKS_FILE = Path(
    "data/processed/knowledge_chunks.jsonl"
)

EMBEDDINGS_FILE = Path(
    "data/processed/knowledge_embeddings.npy"
)

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# --------------------------------------------------
# LIMPIEZA
# --------------------------------------------------

def clean_text(text):
    text = text.replace("\x00", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# --------------------------------------------------
# CHUNKS
# --------------------------------------------------

def split_text(
    text,
    chunk_size=300,
    overlap=60
):
    """
    Divide el texto usando palabras.

    Cada chunk tendrá unas 300 palabras
    y comparte 60 con el anterior.
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


# --------------------------------------------------
# PDF
# --------------------------------------------------

def process_pdf(pdf_path):

    print(
        f"Leyendo: {pdf_path.name}"
    )

    document = fitz.open(
        pdf_path
    )

    chunks = []

    for page_index, page in enumerate(document):

        text = page.get_text(
            "text"
        )

        text = clean_text(text)

        if not text:
            continue

        page_chunks = split_text(
            text
        )

        for chunk_index, chunk in enumerate(
            page_chunks
        ):

            chunks.append(
                {
                    "source": pdf_path.name,

                    # Página del PDF, empezando en 1
                    "page": page_index + 1,

                    "chunk": chunk_index,

                    "text": chunk
                }
            )

    document.close()

    return chunks


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    pdf_files = list(
        PDF_DIR.rglob("*.pdf")
    )

    if not pdf_files:

        print(
            "No encontré PDFs en "
            f"{PDF_DIR}"
        )

        return

    print(
        f"PDFs encontrados: "
        f"{len(pdf_files)}"
    )

    all_chunks = []

    for pdf_file in pdf_files:

        chunks = process_pdf(
            pdf_file
        )

        print(
            f"  -> {len(chunks)} fragmentos"
        )

        all_chunks.extend(
            chunks
        )

    print()
    print(
        f"Fragmentos totales: "
        f"{len(all_chunks)}"
    )

    # ----------------------------------------------
    # Guardar metadata
    # ----------------------------------------------

    CHUNKS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        CHUNKS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for chunk in all_chunks:

            file.write(
                json.dumps(
                    chunk,
                    ensure_ascii=False
                )
                + "\n"
            )

    # ----------------------------------------------
    # Embeddings
    # ----------------------------------------------

    print()
    print(
        "Cargando modelo de embeddings..."
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    print(
        "Generando embeddings..."
    )

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    np.save(
        EMBEDDINGS_FILE,
        embeddings
    )

    print()
    print(
        "=== ÍNDICE COMPLETADO ==="
    )

    print(
        f"Chunks: {len(all_chunks)}"
    )

    print(
        f"Embeddings: "
        f"{embeddings.shape}"
    )

    print(
        f"Metadata: {CHUNKS_FILE}"
    )

    print(
        f"Vectores: {EMBEDDINGS_FILE}"
    )


if __name__ == "__main__":
    main()