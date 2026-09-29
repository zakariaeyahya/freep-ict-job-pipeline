FROM ollama/ollama:latest

ARG OLLAMA_MODEL=qwen2.5:7b-instruct
ENV OLLAMA_MODEL=${OLLAMA_MODEL}

RUN ollama serve & server_pid=$!; \
    for attempt in $(seq 1 60); do \
      if ollama list >/dev/null 2>&1; then break; fi; \
      sleep 2; \
    done; \
    ollama pull "${OLLAMA_MODEL}"; \
    kill "${server_pid}"; \
    wait "${server_pid}" || true