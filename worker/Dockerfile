FROM python:3.10-slim
WORKDIR /app
COPY worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/ .
# Playwright browser binaries
RUN playwright install --with-deps
CMD ["python", "scraper/simple_scraper.py"]