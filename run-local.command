#!/bin/bash
set -e
cd "$(dirname "$0")"
exec .venv/bin/python -c 'import uvicorn; from src.infrastructure.config.settings import settings; uvicorn.run("src.app:app", host="127.0.0.1", port=settings.server_port)'
