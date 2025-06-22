# YouTube RAG Application

An end-to-end Retrieval-Augmented Generation (RAG) application that allows users to query YouTube video content using natural language. Built using Python, LangChain, and a local Ollama-hosted LLM (Gemma:2B), it supports channel-level transcript indexing, semantic search, and precise answer generation, through an intuitive Streamlit interface.

---

## Features

- **Semantic QA**
- **Video & Metadata Extraction** 
- **Transcript Fetching (Manual & Auto-Generated)**
- **Knowledge Base Creation**
- **Retrieval Augmented Generation**
- **Streamlit Frontend**

---

## Tech Stack

- **Python** – Core logic
- **Streamlit** – UI for input, data browsing, and chat interaction
- **LangChain** – RAG pipeline and chain abstraction
- **Ollama** – Lightweight LLM inference runtime 
- **Qdrant** – Vector database 

---

## Getting Started

---

### Environment Setup

1. **Create & activate a virtual environment (Windows-bash)**

```
$ python -m venv <venv-name>
$ venv-name\Scripts\activate  
```

2. **Install dependencies**

```
$ pip install -r requirements.txt
```

3. **Start Qdrant** 

```
$ docker run -p 6333:6333 qdrant/qdrant
```

---

4. **Ollama Setup** (Host the Gemma-2B model locally on `localhost:11434`)

Install [Ollama](https://ollama.com/) and set up:

```
$ ollama pull gemma:2b
$ ollama serve
```


5. **Launch the Streamlit App**

```
$ streamlit run app.py
```

---
