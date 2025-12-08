# Scraper Dashboard — README & Project Skeleton

## Overview

This repository contains a production-ready starter for **Automated Web Scraper + Dashboard**. It includes a detailed README, Docker setup, a Django backend that interfaces with MongoDB via `pymongo`, a Playwright-based scraper worker, a Celery scheduler placeholder, and a minimal React frontend.

Use this to boot a local development environment, extend with new scrapers, and deploy to a container host.

---

## Table of contents

* Quickstart (run locally with Docker Compose)
* Development prerequisites
* Environment variables
* Repository structure
* Key files (skeletons)
* Running without Docker (local Python setup)
* Adding a new target site (job config)
* Deployment notes
* Security & legal reminders

---

## Quickstart (Docker Compose)

1. Clone the repo:

```bash
git clone <your-repo-url> scraper-dashboard
cd scraper-dashboard
```

2. Copy `.env.example` to `.env` and edit values (MONGO_URI, SECRET_KEY, etc.).

3. Build and start services:

```bash
docker-compose up --build
```

4. Backend API will be available at `http://localhost:8000`.
   Frontend at `http://localhost:3000`.

5. Run Playwright dependencies (only once for local dev):

```bash
# inside worker container or local environment
playwright install
```

---

## Development prerequisites

* Docker & Docker Compose
* Node.js (for local frontend dev)
* Python 3.10+
* (Optional) MongoDB locally if not using Atlas

---

## Environment variables (`.env.example`)

```ini
# backend
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
MONGO_URI=mongodb://mongo:27017/scraper_db
REDIS_URL=redis://redis:6379/0
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

# worker
MONGO_URI=${MONGO_URI}
```

---

## Repo structure

```
scraper-dashboard/
├─ backend/
│  ├─ Dockerfile
│  ├─ manage.py
│  ├─ requirements.txt
│  ├─ project/
│  │  ├─ __init__.py
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  ├─ asgi.py
│  │  └─ wsgi.py
│  └─ apps/
│     └─ scraper_app/
│        ├─ __init__.py
│        ├─ views.py
│        ├─ serializers.py
│        ├─ tasks.py
│        ├─ admin.py
│        └─ urls.py
├─ worker/
│  ├─ Dockerfile
│  └─ scraper/
│     ├─ jobs/
│     │  └─ example.json
│     └─ simple_scraper.py
├─ frontend/
│  ├─ Dockerfile
│  ├─ package.json
│  └─ src/
│     └─ App.jsx
├─ docker-compose.yml
├─ .env.example
└─ README.md  <-- this file
```

---

## Key files — full skeletons

### `docker-compose.yml`

```yaml
version: '3.8'
services:
  mongo:
    image: mongo:6
    restart: unless-stopped
    volumes:
      - mongo-data:/data/db
  redis:
    image: redis:7
    restart: unless-stopped
  backend:
    build: ./backend
    env_file: .env
    environment:
      - MONGO_URI=${MONGO_URI}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_DEBUG=${DJANGO_DEBUG}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8000:8000"
    depends_on: [mongo, redis]
  worker:
    build: ./worker
    env_file: .env
    environment:
      - MONGO_URI=${MONGO_URI}
    depends_on: [mongo]
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on: [backend]
volumes:
  mongo-data:
```

---

### `backend/Dockerfile`

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

### `backend/requirements.txt`

```
Django>=4.2
djangorestframework
pymongo
python-dotenv
celery[redis]
playwright
gunicorn
```

---

### `backend/manage.py` (skeleton)

```py
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

---

### `backend/project/settings.py` (skeleton)

```py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.scraper_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': ['django.template.context_processors.debug',
                                           'django.template.context_processors.request',
                                           'django.contrib.auth.context_processors.auth',
                                           'django.contrib.messages.context_processors.messages',],},
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Database: we use MongoDB via pymongo directly. No Django ORM config here.

# Static files
STATIC_URL = '/static/'

# Custom settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/scraper_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
```

---

### `backend/project/urls.py`

```py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.scraper_app.urls')),
]
```

---

### `backend/apps/scraper_app/urls.py`

```py
from django.urls import path
from . import views

urlpatterns = [
    path('listings/', views.list_listings, name='list_listings'),
    path('run-job/', views.run_job, name='run_job'),
]
```

---

### `backend/apps/scraper_app/views.py` (skeleton using `pymongo`)

```py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from pymongo import MongoClient
import os

mongo = MongoClient(os.getenv('MONGO_URI', settings.MONGO_URI))
COL = mongo.scraper_db.listings

@api_view(['GET'])
def list_listings(request):
    q = {}
    source = request.GET.get('source')
    if source:
        q['source'] = source
    cursor = COL.find(q).sort('first_seen', -1).limit(500)
    items = []
    for d in cursor:
        items.append({
            'id': str(d.get('_id')),
            'title': d.get('title'),
            'url': d.get('url'),
            'price': d.get('price'),
            'first_seen': d.get('first_seen')
        })
    return Response(items)

@api_view(['POST'])
def run_job(request):
    # Trigger scraper job: simple implementation calls a shell command or enqueues a Celery task.
    job = request.data.get('job')
    # TODO: validate job, enqueue to Celery or call worker endpoint
    return Response({'status': 'scheduled', 'job': job})
```

---

### `backend/apps/scraper_app/tasks.py` (Celery skeleton)

```py
from celery import shared_task
import subprocess

@shared_task
def run_scraper_job(job_config_path):
    # Example: call worker script with job path
    subprocess.run(['python', '/worker/scraper/simple_scraper.py', job_config_path], check=True)
```

---

### `worker/Dockerfile`

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/ .
# Playwright browser binaries
RUN playwright install --with-deps
CMD ["python", "scraper/simple_scraper.py"]
```

---

### `worker/scraper/simple_scraper.py` (Playwright example)

```py
import asyncio
from playwright.async_api import async_playwright
from pymongo import MongoClient
import os
import datetime

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/scraper_db')
client = MongoClient(MONGO_URI)
COL = client.scraper_db.listings

async def scrape(url, selectors):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        items = await page.query_selector_all(selectors.get('item'))
        for it in items:
            try:
                title = await it.query_selector_eval(selectors['title'], 'el => el.innerText')
            except Exception:
                title = None
            try:
                link = await it.query_selector_eval(selectors['link'], 'el => el.href')
            except Exception:
                link = None
            doc = {
                'source': url,
                'title': title,
                'url': link,
                'raw_html': await it.inner_html(),
                'scraped_at': datetime.datetime.utcnow(),
            }
            COL.update_one({'url': link}, {'$set': doc, '$setOnInsert': {'first_seen': datetime.datetime.utcnow()}}, upsert=True)
        await browser.close()

if __name__ == '__main__':
    # Example run reading jobs/example.json
    import json
    with open('jobs/example.json') as f:
        cfg = json.load(f)
    asyncio.run(scrape(cfg['url'], cfg['selectors']))
```

---

### `worker/scraper/jobs/example.json`

```json
{
  "name": "example-listings",
  "url": "https://example.com/listings",
  "selectors": {
    "item": ".item",
    "title": ".title",
    "link": \".title a\"
  }
}
```

---

### `frontend/Dockerfile` (minimal)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
EXPOSE 3000
CMD ["npm", "start"]
```

---

### `frontend/src/App.jsx` (skeleton)

```jsx
import React, {useEffect, useState} from 'react'

export default function App(){
  const [items, setItems] = useState([])
  useEffect(()=>{ fetch('/api/listings/').then(r=>r.json()).then(setItems) }, [])
  return (
    <div style={{padding:20}}>
      <h1>Scraped Listings</h1>
      <table>
        <thead><tr><th>Title</th><th>URL</th><th>First seen</th></tr></thead>
        <tbody>
          {items.map(i => (
            <tr key={i.id}><td>{i.title}</td><td><a href={i.url}>{i.url}</a></td><td>{i.first_seen}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## Running without Docker (local)

1. Create a virtualenv and install requirements from `backend/requirements.txt`.
2. Set `MONGO_URI` to your local or Atlas URI.
3. `python manage.py runserver` to run backend.
4. Run worker: `python worker/scraper/simple_scraper.py` (after installing Playwright and running `playwright install`).

---

## Adding a new target site (job config)

1. Create a JSON config under `worker/scraper/jobs/` with keys: `name`, `url`, `selectors`.
2. Test locally by running the scraper against that config.
3. Add an entry to backend job registry (future enhancement) to allow scheduling.

---

## Deployment notes

* Use MongoDB Atlas for production database.
* Host backend and worker on a container platform (Render, Railway, Fly.io).
* Host frontend on Vercel or serve static build from backend.
* Use a managed Redis for Celery in production.

---

## Security & legal reminders

* Respect `robots.txt` and target site TOS.
* Avoid scraping private user data or sites that forbid scraping.
* Implement rate-limits and configure polite request intervals.

---

## Next steps I can generate now

* Full `backend/` Django project files (ready-to-run)
* `docker-compose.yml` with production-ready env examples
* A Playwright scraping framework that supports CSS/XPath configs

Select which of those to generate and I will add them to the repository.
