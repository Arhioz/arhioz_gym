FROM python:3.12-slim

WORKDIR /app

# Prevenir archivos .pyc y forzar salida de logs sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instalación de requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del código fuente de la aplicación
COPY . .

EXPOSE 8000

# Ejecución en modo producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]