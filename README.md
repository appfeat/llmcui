# LLMCUI

LLMCUI is a lightweight session engine for Simon Willison’s `llm` command-line tool.  
It provides persistent projects, structured multi-chat sessions, and automatic context management using an SQLite backend and a character-based interface (CUI).

LLMCUI enhances the standard `llm` workflow by adding long-term memory, organized workspaces, project-level context, and reproducible chat histories—all while remaining terminal-native and automation-friendly.

Repository: https://github.com/appfeat/llmcui.git

---------------------------------------------------------------------

## Features

- Project management  
  Organize conversations into named workspaces.

- Multi-chat support  
  Each project can contain multiple isolated chat threads.

- Automatic context assembly  
  LLMCUI retrieves distilled summaries and recent messages to create an optimized prompt for each request.

- Background distillation  
  Summaries are automatically compressed to reduce token usage.

- SQLite-backed persistence  
  All messages, chats, and summaries are stored in one database.

- Silent-by-default CUI  
  Interactive prompts appear only when necessary.

- Works over SSH / Termux  
  No GUI dependencies.

---------------------------------------------------------------------

## Requirements

- Python 3.10+
- SQLite3
- Simon Willison’s `llm` tool (>= 0.27.1)

Install llm:

    pip install -U llm

Optional:

    pip install rich click tiktoken

---------------------------------------------------------------------

## Installation

Clone the repository:

    git clone https://github.com/appfeat/llmcui.git ~/.llmcui
    cd ~/.llmcui

Initialize the database:

    python3 db/init_db.py

Make entrypoint executable:

    chmod +x ai.py

Create global symlink:

    sudo ln -sf ~/.llmcui/ai.py /usr/local/bin/ai

Test:

    ai "hello"

---------------------------------------------------------------------

## Usage

### Basic query

    ai "Explain RAG in one paragraph."

LLMCUI will:
1. Resolve project + chat
2. Load summaries
3. Load recent messages
4. Build optimized context
5. Call llm prompt
6. Save messages
7. Trigger distillation

### New project

    ai -p research "Start a literature review."

### Select chat

    ai -c 2 "Continue."

### Reset chat

    ai -r "Begin again."

---------------------------------------------------------------------

## Directory Structure

~/.llmcui/
    ai.py
    config.py
    db/
        init_db.py
        models.py
        queries.py
    core/
        logic.py
        context.py
        distill.py
    llm/
        client.py
        prompts.py

---------------------------------------------------------------------

## Database Layout

Stored in ~/.llmcui/llmcui.db:

- projects
- chats
- messages
- distilled_chat
- distilled_project
- debug_log
- state

---------------------------------------------------------------------

## Debugging

List projects:

    sqlite3 ~/.llmcui/llmcui.db "SELECT * FROM projects;"

Recent messages:

    sqlite3 ~/.llmcui/llmcui.db "SELECT role, content FROM messages ORDER BY id DESC LIMIT 10;"

Summaries:

    sqlite3 ~/.llmcui/llmcui.db "SELECT * FROM distilled_chat;"

---------------------------------------------------------------------

## Why LLMCUI

LLMCUI introduces structured, persistent memory to Simon Willison’s `llm`, enabling:

- long-term project workflows
- multiple chat threads
- optimized prompt contexts
- consistent organization
- reduced token usage

All within a terminal-native environment suited for SSH, Termux, and automation pipelines.
