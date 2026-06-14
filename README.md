# AI Knowledge Assistant API (FastAPI + ngrok)

## Run
1) Install deps:
```bash
pip install -r requirements.txt
```

2) Start Ollama + pull model:
```bash
ollama serve
ollama pull llama3
```

3) Start API:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Expose with ngrok
```bash
ngrok http 8000
```

## Endpoints
- GET /health
- POST /process (multipart form: files/text/link)
- POST /qa (multipart form: question)
