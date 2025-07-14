# Usa una imagen base ligera de Python 3.11
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de dependencias
COPY . .

# Instala dependencias del sistema necesarias para pandas y SQLite
RUN pip install --no-cache-dir -r requirements.txt

# Comando para arrancar la API
CMD ["python","streamlit","run","app.py"]
