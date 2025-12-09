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