# Jarvis

Jarvis es un asistente personal local desarrollado para experimentar con modelos de lenguaje, recuperación de información y personalización del estilo de respuesta.

El proyecto combina un modelo local ejecutado con Ollama, un sistema de RAG para consultar libros y papers, un perfil de estilo construido a partir de mensajes propios y una interfaz web desarrollada con Next.js.

Todo el procesamiento principal se realiza localmente.

---

## Objetivo

El objetivo del proyecto es construir un asistente personal que pueda:

- Conversar de forma natural.
- Adaptarse al estilo de escritura del usuario.
- Consultar libros, apuntes y papers.
- Ayudar con física, matemática y temas académicos.
- Mostrar fuentes y páginas utilizadas.
- Renderizar correctamente Markdown, código y expresiones matemáticas en LaTeX.
- Utilizar modelos locales mediante Ollama.

A futuro, el proyecto puede extenderse con memoria, herramientas matemáticas, manejo de documentos desde la interfaz y distintos modos de razonamiento.

---

## Arquitectura

El proyecto está dividido principalmente en dos partes:

```text
jarvis/
├── personal-ai/
│   ├── backend/
│   ├── src/
│   ├── data/
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── ...
│
└── README.md
```

### Backend

El backend está desarrollado en Python.

Se encarga de:

- Comunicación con Ollama.
- Carga del modelo de embeddings.
- Recuperación de ejemplos de estilo.
- Búsqueda semántica y léxica.
- RAG sobre documentos.
- Historial de conversación.
- Construcción del prompt.
- Exposición de una API mediante FastAPI.

### Frontend

El frontend está desarrollado con Next.js y TypeScript.

Se encarga de:

- Interfaz de chat.
- Envío de mensajes al backend.
- Manejo visual del historial.
- Renderizado de Markdown.
- Renderizado de LaTeX con KaTeX.
- Visualización opcional de fuentes académicas.

---

# Tecnologías

## Backend

- Python
- FastAPI
- Uvicorn
- Ollama
- NumPy
- scikit-learn
- Sentence Transformers
- PyMuPDF
- TF-IDF
- embeddings semánticos

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- react-markdown
- remark-math
- rehype-katex
- KaTeX

---

# Modelo local

Actualmente Jarvis utiliza:

```text
qwen3.5:9b
```

mediante Ollama.

El modelo puede cambiarse desde:

```text
personal-ai/src/llm/local_model.py
```

Por ejemplo:

```python
MODEL = "qwen3.5:9b"
```

---

# Personalización del estilo

Jarvis utiliza mensajes propios previamente procesados para aprender patrones del estilo de escritura.

El sistema utiliza:

- estadísticas de estilo;
- ejemplos reales de conversación;
- embeddings;
- búsqueda semántica;
- TF-IDF;
- recuperación híbrida.

Los ejemplos recuperados se utilizan como referencia de tono y forma de respuesta, no como fuente factual.

---

# RAG académico

Los documentos académicos se almacenan localmente en:

```text
personal-ai/data/papers/
```

Se pueden agregar:

- libros;
- papers;
- apuntes;
- documentos académicos en PDF.

Después de agregar nuevos documentos es necesario reconstruir el índice:

```powershell
cd personal-ai
python src/rag/build_pdf_index.py
```

El proceso genera archivos como:

```text
data/processed/knowledge_chunks.jsonl
data/processed/knowledge_embeddings.npy
```

Jarvis utiliza búsqueda híbrida:

```text
70% similitud semántica
30% similitud léxica
```

Esto permite combinar comprensión del significado con coincidencias exactas de términos académicos.

---

# API

El backend expone una API local con FastAPI.

Por defecto:

```text
http://127.0.0.1:8000
```

La documentación automática está disponible en:

```text
http://127.0.0.1:8000/docs
```

## Endpoint principal

```http
POST /chat
```

Ejemplo:

```json
{
  "message": "Explicame las ecuaciones de Cauchy Riemann",
  "history": []
}
```

Respuesta:

```json
{
  "answer": "Las ecuaciones son...",
  "model": "qwen3.5:9b",
  "sources": [
    {
      "source": "Brown-Churchill.pdf",
      "page": 78,
      "similarity": 0.52
    }
  ]
}
```

---

# Instalación

## Requisitos

Es necesario tener instalado:

- Python
- Node.js
- npm
- Ollama
- Git

---

## Backend

Entrar a:

```powershell
cd personal-ai
```

Instalar dependencias principales:

```powershell
python -m pip install fastapi uvicorn requests numpy scikit-learn sentence-transformers pymupdf
```

Instalar o descargar el modelo de Ollama:

```powershell
ollama pull qwen3.5:9b
```

Iniciar el backend:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

---

## Frontend

Entrar a:

```powershell
cd frontend
```

Instalar dependencias:

```powershell
npm install
```

Si es necesario instalar el soporte de Markdown y LaTeX:

```powershell
npm install react-markdown remark-math rehype-katex katex
```

Iniciar:

```powershell
npm run dev
```

La interfaz estará disponible en:

```text
http://localhost:3000
```

---

# Flujo general

```text
Usuario
   │
   ▼
Next.js
   │
   │ POST /chat
   ▼
FastAPI
   │
   ├── Perfil de estilo
   ├── Ejemplos de conversación
   ├── RAG académico
   ├── Historial
   │
   ▼
Ollama
   │
   ▼
Qwen
   │
   ▼
Respuesta
   │
   ├── Markdown
   ├── LaTeX
   └── Fuentes
   │
   ▼
Frontend
```

---

# Fórmulas matemáticas

Jarvis puede devolver expresiones matemáticas en LaTeX.

Ejemplo:

```md
$$
u_x = v_y
$$

$$
u_y = -v_x
$$
```

El frontend las renderiza utilizando KaTeX.

---

# Fuentes

Cuando Jarvis utiliza material académico, la API también devuelve las fuentes recuperadas.

La interfaz permite mantenerlas ocultas por defecto y mostrarlas cuando sea necesario.

Ejemplo:

```text
Mostrar fuentes (4)
```

---

# Privacidad

El proyecto está diseñado para trabajar localmente.

Los siguientes datos no deberían subirse al repositorio:

```text
personal-ai/data/raw/
personal-ai/data/processed/
personal-ai/data/papers/
personal-ai/models/
personal-ai/vector_db/
```

También deben ignorarse:

```text
frontend/node_modules/
frontend/.next/
```

Los chats personales, documentos y embeddings permanecen localmente.

---

# Estado actual

Actualmente Jarvis puede:

- usar un modelo local mediante Ollama;
- mantener historial de conversación;
- imitar parcialmente el estilo de escritura del usuario;
- consultar múltiples PDFs;
- recuperar fragmentos relevantes;
- indicar fuente y página;
- responder preguntas académicas;
- generar expresiones en LaTeX;
- mostrar Markdown y código;
- funcionar mediante una API;
- utilizar una interfaz web en Next.js.

---

# Próximas mejoras

Algunas mejoras planeadas:

- Historial persistente de conversaciones.
- Sidebar con chats anteriores.
- Gestión de papers desde la interfaz.
- Subida de PDFs.
- Reindexado automático.
- Selector de modelo.
- Modo rápido y modo razonamiento.
- Activar RAG solamente cuando sea necesario.
- Visualización más avanzada de fuentes.
- Memoria a largo plazo.
- Integración con SymPy.
- Herramientas para resolver problemas matemáticos.
- Streaming de respuestas.
- Mejor recuperación y reranking de documentos.

---

# Uso

Para iniciar el sistema actualmente se deben ejecutar el backend y el frontend.

Backend:

```powershell
cd personal-ai
python -m uvicorn backend.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Luego abrir:

```text
http://localhost:3000
```

---

## Autor

Proyecto personal de experimentación con inteligencia artificial, modelos locales, NLP, RAG y herramientas académicas.
```

Yo lo guardaría directamente como:

```text
jarvis/README.md
```

y haría luego:

```powershell
git add README.md
git commit -m "Add project README"
git push
```
