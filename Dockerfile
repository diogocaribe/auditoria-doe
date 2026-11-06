# Use the official Python image from the Docker Hub
FROM python:3.12-slim

WORKDIR /auditoria-doe

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install poetry and project dependencies
RUN pip install --no-cache-dir poetry 

COPY pyproject.toml poetry.lock /auditoria-doe/
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["poetry", "run", "streamlit", "run", "auditoria-doe/app.py", "--server.port=8501", "--server.address=0.0.0.0"]