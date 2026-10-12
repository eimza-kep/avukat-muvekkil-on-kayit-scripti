FROM python:3.12-alpine

WORKDIR /app

# Dosyaları kopyala
COPY . /app

# SQLite veritabanı klasörü izinleri
RUN chmod -R 755 /app

ENV PORT=8082
EXPOSE 8082

CMD ["python", "server.py"]
