from pathlib import Path
import json

import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_FILE = Path("data/processed/style_examples.jsonl")
EMBEDDINGS_FILE = Path("data/processed/style_embeddings.npy")
CLEAN_EXAMPLES_FILE = Path(
    "data/processed/style_examples_clean.jsonl"
)

MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


def main():
    examples = []
    contexts = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:
            example = json.loads(line)

            context = example["context"].strip()
            response = example["response"].strip()

            if not context or not response:
                continue

            examples.append(example)
            contexts.append(context)

    print(f"Ejemplos cargados: {len(examples)}")
    print("Cargando modelo de embeddings...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Generando embeddings...")

    embeddings = model.encode(
        contexts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    EMBEDDINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    np.save(
        EMBEDDINGS_FILE,
        embeddings
    )

    with open(
        CLEAN_EXAMPLES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for example in examples:
            file.write(
                json.dumps(
                    example,
                    ensure_ascii=False
                )
                + "\n"
            )

    print()
    print("=== EMBEDDINGS CREADOS ===")
    print()
    print(f"Cantidad de ejemplos: {len(examples)}")
    print(f"Dimensiones: {embeddings.shape}")
    print(f"Embeddings: {EMBEDDINGS_FILE}")
    print(f"Ejemplos limpios: {CLEAN_EXAMPLES_FILE}")


if __name__ == "__main__":
    main()