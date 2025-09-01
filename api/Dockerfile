FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p api
RUN touch api/__init__.py

RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app

COPY --chown=app:app . .

USER app

RUN mkdir -p /home/app/nltk_data
ENV NLTK_DATA=/home/app/nltk_data

RUN python -c "import nltk; nltk.download('punkt', download_dir='/home/app/nltk_data'); nltk.download('stopwords', download_dir='/home/app/nltk_data'); nltk.download('wordnet', download_dir='/home/app/nltk_data')"

EXPOSE 5050

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5050"]