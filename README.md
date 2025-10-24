# MVC Console Chatbot

This repository contains a minimal Model-View-Controller (MVC) style console chatbot
that calls OpenAI's Chat Completions API. The project is intentionally lightweight so
you can focus on understanding how the controller coordinates the view (terminal UI)
and model (API integration).

## Project Structure

```
main.py              # Application entry point and dependency wiring
controller/          # ChatController orchestrates the conversation loop
model/               # AIEngine handles OpenAI API requests
view/                # ConsoleUI manages terminal input/output
```

## Requirements

- Python 3.11+
- An OpenAI API key available as the `OPENAI_API_KEY` environment variable
- The [`requests`](https://requests.readthedocs.io/) library

Install dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests
```

## Usage

1. (Optional) Store your API key in a `keys.env` file in the project root, formatted as
   `OPENAI_API_KEY=sk-...`. The application loads this file automatically when it
   starts.
2. Run the chatbot:

```bash
python main.py
```

Type questions at the prompt and enter `exit` to end the conversation.
