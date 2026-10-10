FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Solo entra a la imagen lo que la aplicación necesita para funcionar (no documentos, pruebas,
# herramientas de desarrollo ni archivos de configuración local).
COPY run.py .
COPY app ./app

# La aplicación no corre como administrador del contenedor.
RUN useradd --create-home --shell /usr/sbin/nologin gestlab
USER gestlab

ENV PORT=5000
EXPOSE ${PORT}

CMD ["python", "run.py"]
