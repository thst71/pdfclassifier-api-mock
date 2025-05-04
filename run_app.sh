#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the application
uvicorn --app-dir src openapi_server.main:app --reload --host 0.0.0.0 --port 8080

# Deactivate the virtual environment when the application is stopped
deactivate