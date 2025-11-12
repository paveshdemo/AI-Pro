# Neuro AI Web Experience

Neuro AI is a polished web interface for exploring OpenAI-powered conversations in a
dark, purple-themed environment. The original MVC console chatbot has been upgraded
with a modern Flask application so you can chat with your assistant right from the
browser.

## Project Structure

```
main.py              # Application entry point for the Flask development server
web_app.py           # Flask application factory and API endpoints
templates/           # Jinja2 templates (Neuro AI interface)
static/              # Compiled assets (CSS & JavaScript)
controller/          # Legacy console controller (retained for reference)
model/               # AIEngine handles OpenAI API requests
view/                # Legacy console UI (retained for reference)
```

## Requirements

- Python 3.11+
- An OpenAI API key available as the `OPENAI_API_KEY` environment variable
- The [`requests`](https://requests.readthedocs.io/) and
  [`Flask`](https://flask.palletsprojects.com/) libraries

Install dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

1. (Optional) Store your API key in a `keys.env` file in the project root, formatted as
   `OPENAI_API_KEY=sk-...`. The application loads this file automatically when it
   starts.
2. Start the Neuro AI web experience:

```bash
python main.py
```

3. Open <http://127.0.0.1:8000> in your browser and begin chatting with Neuro AI.

The original console components remain in the repository if you would like to study
or extend the MVC implementation.

## Personalising with Lecture Notes

Neuro AI can ground its answers in your own lecture material. Use the ingestion
script to embed any PDF into the local document store:

```bash
python scripts/ingest_document.py /path/to/lecture.pdf --title "Week 05 - Databases"
```

Behind the scenes the script extracts the PDF text, generates OpenAI embeddings,
and stores them in `data/document_index.json`. When you next chat with Neuro AI
the assistant will automatically retrieve the most relevant lecture snippets and
inject them into the system prompt so responses stay aligned with the SLIIT
curriculum.

## Custom Project Files

For bespoke study material or project notes, add your own PDFs to the
`project_files/` directory in the repository root. Once you have copied files into
this folder, sync them with the document store:

```bash
python scripts/ingest_project_files.py
```

The script discovers every PDF in the folder (including nested directories) and
processes them in one go. After the embeddings are generated, Neuro AI will surface
relevant excerpts from your documents during conversations for more tailored answers.
