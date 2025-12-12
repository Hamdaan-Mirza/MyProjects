FROM python:3.10-slim
WORKDIR /app

# Install dependencies first (cached unless requirements.txt changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (cached unless dependencies change)
RUN playwright install --with-deps chromium

# Copy code LAST (this layer changes most frequently)
COPY . .

CMD ["python", "scraper/scraper.py"]