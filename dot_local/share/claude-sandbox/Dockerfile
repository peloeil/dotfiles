FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

RUN mkdir -p /claude-home && chmod 777 /claude-home

WORKDIR /workspace
ENTRYPOINT ["claude"]
