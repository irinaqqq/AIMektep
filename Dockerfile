FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -ms /bin/bash appuser

RUN chown -R appuser:appuser /src

USER appuser

CMD ["bash", "-c", "cd src && uvicorn main:app --host 0.0.0.0 --port 8888"]
