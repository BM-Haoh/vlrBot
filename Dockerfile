FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Copia e instala apenas as dependências do BOT
COPY requirements_bot.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2. Em vez de COPY . ., copiamos APENAS os arquivos fundamentais do bot
COPY brain.py ./brain.py
# Caso sua estrutura de bot use arquivos direto na src/ (como main.py, disc_buttons.py):
COPY src/main.py ./src/main.py
COPY src/disc_buttons.py ./src/disc_buttons.py

# Define o caminho de execução padrão
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "src/main.py"]