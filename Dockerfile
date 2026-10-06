FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar os arquivos do projeto
COPY . .

# Variáveis de ambiente padrão para nuvem (podem ser sobrescritas)
ENV PYTHONUNBUFFERED=1

# Expor a porta 8080 (App Runner, Beanstalk, ECS padrão)
EXPOSE 8080

# Iniciar com Gunicorn usando src.web:app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "src.web:app"]
