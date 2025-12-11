import asyncio
from playwright.async_api import async_playwright
from pymongo import MongoClient
import os
import datetime

# Reuse your existing DB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/scraper_db')
client = MongoClient(MONGO_URI)
COL = client.scraper_db.listings

async def scrape_google_maps(search_query, total_needed=10):
    """
    Specialized scraper for Google Maps Business listings.
    """
    async with async_playwright() as p:
        # Launch browser (headless=False is better for debugging Maps, but True for prod)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        # 1. Navigate to Google Maps
        print(f"Searching Google Maps for: {search_query}")
        await page.goto("https://www.google.com/maps", timeout=60000)
        
        # 2. Type search term and press Enter
        # (Google Maps IDs change, but 'searchboxinput' is relatively stable)
        await page.wait_for_selector("input#searchboxinput")
        await page.fill("input#searchboxinput", search_query)
        await page.keyboard.press("Enter")

        # 3. Wait for the sidebar results to load
        # This checks for the main feed container in the sidebar
        await page.wait_for_selector('div[role="feed"]', timeout=15000)

        items_scraped = 0
        previously_counted = 0
        
        while items_scraped < total_needed:
            # 4. Extract current list of items
            listings = await page.locator('div[role="article"]').all()
            
            # 5. Process new items
            for listing in listings[items_scraped:]:
                try:
                    # Extract basic details (Selectors here are heuristic and may need maintenance)
                    aria_label = await listing.get_attribute("aria-label")
                    if not aria_label: continue # Skip ads or spacers
                    
                    # Store data
                    doc = {
                        'source': 'google_maps',
                        'job_query': search_query,
                        'title': aria_label,
                        'url': f"https://www.google.com/maps/search/{aria_label}", # Constructed URL
                        'raw_html': 'maps_data', # Keeping it light
                        'scraped_at': datetime.datetime.utcnow(),
                    }
                    
                    # Save to DB (Using title + query as unique key since URLs vary)
                    COL.update_one(
                        {'title': aria_label, 'job_query': search_query}, 
                        {'$set': doc, '$setOnInsert': {'first_seen': datetime.datetime.utcnow()}}, 
                        upsert=True
                    )
                    items_scraped += 1
                    if items_scraped >= total_needed: break
                    
                except Exception as e:
                    print(f"Error parsing item: {e}")

            # 6. Scroll Logic (Crucial for Maps)
            # You must scroll the *feed*, not the page
            if items_scraped == previously_counted:
                # If we haven't found new items, force a scroll on the sidebar
                feed = page.locator('div[role="feed"]')
                await feed.evaluate("el => el.scrollBy(0, 1000)")
                await page.wait_for_timeout(2000) # Give it time to load dynamic content
                
                # Check if we hit the end (optional: check for 'You've reached the end')
            
            previously_counted = items_scraped
            print(f"Scraped {items_scraped}/{total_needed}...")

        await browser.close()