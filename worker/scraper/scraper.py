"""
Worker polling loop - reads jobs from MongoDB and executes scraper.
"""

import time
import asyncio
import os
from pymongo import MongoClient
from datetime import datetime

# IMPORTS: Rename your original scraper to 'scrape_simple' to verify which one is running
from simple_scraper import scrape as scrape_simple
# IMPORT: The new Google Maps scraper we designed
from google_maps_scraper import scrape_google_maps


MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/scraper_db')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '10'))


def poll_and_run():
    """Poll MongoDB for pending jobs and execute them."""
    client = MongoClient(MONGO_URI)
    jobs_col = client.scraper_db.jobs
    
    print(f"Worker started. Polling every {POLL_INTERVAL}s for jobs...")
    
    while True:
        try:
            # Find a pending job and mark it as running
            job_doc = jobs_col.find_one_and_update(
                {'status': 'pending'},
                {'$set': {'status': 'running', 'started_at': datetime.utcnow()}},
                sort=[('created_at', 1)]
            )
            
            if job_doc:
                job_id = str(job_doc['_id'])
                job_data = job_doc.get('job', {})
                print(f"Processing job {job_id}: {job_data}")
                
                try:
                    # --- ROUTING LOGIC START ---
                    # Check the 'type' field in the job payload. Default to 'simple' for backward compatibility.
                    job_type = job_data.get('type', 'simple')
                    
                    if job_type == 'google_maps':
                        # Validating specific fields for Google Maps
                        query = job_data.get('query')
                        # Default to 10 if not provided
                        limit = int(job_data.get('limit', 10)) 
                        
                        if not query:
                            raise ValueError("Google Maps job missing 'query' parameter")
                            
                        print(f"Running Google Maps scraper for: {query}")
                        count = asyncio.run(scrape_google_maps(query, limit))

                    else:
                        # Existing Simple Scraper Logic (Generic)
                        url = job_data.get('url')
                        selectors = job_data.get('selectors', {})
                        
                        if not url or not selectors:
                            raise ValueError("Simple job missing 'url' or 'selectors'")
                        
                        print(f"Running Simple scraper for: {url}")
                        count = asyncio.run(scrape_simple(url, selectors))
                    # --- ROUTING LOGIC END ---
                    
                    # Mark as completed
                    jobs_col.update_one(
                        {'_id': job_doc['_id']},
                        {'$set': {'status': 'completed', 'completed_at': datetime.utcnow(), 'count': int(count) if 'count' in locals() else None}}
                    )
                    print(f"Job {job_id} completed successfully")
                    
                except Exception as e:
                    print(f"Job {job_id} failed: {e}")
                    jobs_col.update_one(
                        {'_id': job_doc['_id']},
                        {'$set': {'status': 'failed', 'error': str(e), 'failed_at': datetime.utcnow()}}
                    )
            else:
                # No pending jobs, wait before polling again
                time.sleep(POLL_INTERVAL)
                
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    poll_and_run()