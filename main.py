import os
import tempfile
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
import gdown
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import speech_recognition as sr

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, UnstructuredFileLoader
)

# --- UPDATED LANGCHAIN IMPORTS ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
# ---------------------------------

app = FastAPI(title="AI Knowledge Assistant API")

# Security middleware to allow Streamlit UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_DB = None

def load_file(path: str):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(path).load()
    elif ext == ".txt":
        return TextLoader(path, encoding="utf-8").load()
    elif ext == ".csv":
        return CSVLoader(path).load()
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
        content = "\n".join(df.astype(str).agg(" ".join, axis=1))
        return [Document(page_content=content)]
    elif ext in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]:
        recognizer = sr.Recognizer()
        wav_file = "temp_audio.wav"
        AudioSegment.from_file(path).export(wav_file, format="wav")
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="ar-EG")
        return [Document(page_content=text)]
    else:
        return UnstructuredFileLoader(path).load()

def load_url(url: str):
    if "drive.google.com" in url:
        output = "temp_drive_file"
        gdown.download(url, output, quiet=False)
        return load_file(output)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        r = requests.get(url, timeout=30, headers=headers)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            if not text:
                text = r.text
            return [Document(page_content=text)]
        else:
            print(f"DEBUG: URL {url} returned status {r.status_code}")
    except Exception as e:
        print(f"DEBUG: URL exception: {e}")
        return []
    return []

def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(docs)

def build_vector_db(chunks):
    # Using the new HuggingFace package
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(chunks, embeddings)

def get_llm(temp: float = 0.0):
    # Using the new Ollama package
    return ChatOllama(model="llama3", temperature=temp)

def summarize_docs(docs):
    llm = get_llm(0.2)
    prompt = ChatPromptTemplate.from_template(
        """Write a detailed summary of the following text (Arabic+English):\n\n{text}"""
    )
    chain = prompt | llm | StrOutputParser()
    full_text = "\n\n".join(d.page_content for d in docs)
    return chain.invoke({"text": full_text})

def ask_question(db, question: str):
    retriever = db.as_retriever(search_kwargs={"k": 5})
    llm = get_llm(0)
    prompt = ChatPromptTemplate.from_template(
        """Answer the question in detail using ONLY the context below.\n\nContext:\n{context}\n\nQuestion:\n{question}"""
    )
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain.invoke(question)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    return {"ok": True, "kb_ready": VECTOR_DB is not None}

@app.post("/process")
async def process_inputs(
    files: Optional[List[UploadFile]] = File(default=None),
    text: Optional[str] = Form(default=None),
    link: Optional[str] = Form(default=None),
):
    global VECTOR_DB
    documents = []
    tmp_paths = []

    try:
        if files:
            for f in files:
                suffix = Path(f.filename).suffix or ""
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    data = await f.read()
                    tmp.write(data)
                    tmp_paths.append(tmp.name)
                documents.extend(load_file(tmp_paths[-1]))

        if text and text.strip():
            documents.append(Document(page_content=text.strip()))

        if link and link.strip():
            link = link.strip()
            # Processes standard Web and Google Drive links safely
            documents.extend(load_url(link))

        if not documents:
            if files or text or link:
                raise HTTPException(status_code=400, detail="Input was provided, but no text could be extracted. Check if the link is accessible or if the file is empty/unsupported.")
            raise HTTPException(status_code=400, detail="No input provided (files/text/link).")

        chunks = split_docs(documents)
        summary = summarize_docs(chunks)
        VECTOR_DB = build_vector_db([Document(page_content=summary)])

        return {"summary": summary, "status": "✅ Knowledge base ready (summary stored for Q&A)"}

    finally:
        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass

@app.post("/qa")
def qa(question: str = Form(...)):
    global VECTOR_DB
    if VECTOR_DB is None:
        raise HTTPException(status_code=400, detail="Process inputs first (/process).")
    answer = ask_question(VECTOR_DB, question)
    return {"answer": answer}