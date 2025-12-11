FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Playwright browser binaries
RUN playwright install --with-deps
CMD ["python", "scraper/scraper.py"]