# AI Knowledge Assistant

A FastAPI-based knowledge processing system with local LLM integration (Ollama), file support, and ngrok tunneling.

## Features

- Process text, files (PDF, images), and web links
- Local LLM integration with Ollama
- Question answering based on processed knowledge
- Expose API publicly using ngrok

## Installation

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and start Ollama

Download Ollama from [ollama.ai](https://ollama.ai) then:

```bash
ollama serve
```

### 3. Pull a model

```bash
ollama pull llama3
```

## Running the API

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Expose with ngrok

Download ngrok from [ngrok.com](https://ngrok.com) then:

```bash
ngrok http 8000
```

## API Endpoints

### GET /health
Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

### POST /process
Upload files, text, or links to process.

**Parameters (multipart/form-data):**
- `files` - One or more files (PDF, TXT, images)
- `text` - Direct text input
- `link` - URL to a webpage

**Example:**
```bash
curl -X POST http://localhost:8000/process \
  -F "files=@document.pdf" \
  -F "text=AI is transforming healthcare"
```

### POST /qa
Ask questions about processed knowledge.

**Parameters (multipart/form-data):**
- `question` - Your question (required)

**Example:**
```bash
curl -X POST http://localhost:8000/qa \
  -F "question=What is the main topic?"
```

## Interactive Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Requirements

Create `requirements.txt`:

```txt
fastapi
uvicorn
python-multipart
requests
PyPDF2
pillow
httpx
```

## Project Structure

```
AI_Knowledge_Assistant/
├── main.py
├── requirements.txt
└── README.md
```

## Notes

- Ollama must be running before starting the API
- The API stores processed knowledge in memory by default
- Use ngrok to expose your local API to the internet

## License

MIT
