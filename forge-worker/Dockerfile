FROM python:3.12-slim

# Instala git, bash, curl, nodejs (para Gemini CLI)
RUN apt-get update && apt-get install -y \
    git \
    bash \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Instala o Gemini CLI globalmente
RUN npm install -g @google/gemini-cli

# Configura git para operações não-interativas
RUN git config --global user.email "forge@erp-dsl.bot" && \
    git config --global user.name "Forge Agent"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Diretório de workspace isolado para clones
RUN mkdir -p /workspace

EXPOSE 8020

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]
