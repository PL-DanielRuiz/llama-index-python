FROM python:3.11 as build

WORKDIR /app

ENV PYTHONPATH=/app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Chromium for web loader
# Can disable this if you don't use the web loader to reduce the image size
RUN apt update && apt install -y chromium chromium-driver

# Install dependencies
COPY ./pyproject.toml ./poetry.lock* /app/
RUN poetry install --no-root --no-cache --only main

# ====================================
FROM build as release

COPY . .

CMD ["python", "main.py"]


# # ====================================
# # Etapa de desarrollo
# FROM build as dev

# # Instalar dependencias de desarrollo
# RUN poetry install --no-root --no-cache --only main,dev

# # Copiar el código fuente
# COPY . .

# # Configurar comando para ejecutar en modo desarrollo
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]