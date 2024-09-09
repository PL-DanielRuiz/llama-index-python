# backend
FROM python:3.11 as build

WORKDIR /app

ENV PYTHONPATH=/app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Chromium for web loader
RUN apt update && apt install -y chromium chromium-driver

# Install dependencies
COPY ./pyproject.toml ./poetry.lock* /app/
RUN poetry install --no-root --no-cache --only main

# ====================================
# FROM build as dev

# # Install development dependencies
# RUN poetry install --no-root --no-cache --only main,dev

# # Copy the application code
# COPY . .

# # Expose ports for development and debugging
# EXPOSE 8000 5678

# # Command to run the application in development mode with debugging enabled
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]