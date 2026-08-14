FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY README.md ./

RUN python -m pip install --no-cache-dir .

EXPOSE 8501

CMD ["streamlit", "run", "src/agent_harness/web/theater.py", "--server.address=0.0.0.0", "--server.port=8501"]