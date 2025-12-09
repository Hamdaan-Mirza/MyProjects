"""
Worker polling loop - reads jobs from MongoDB and executes scraper.
"""
import time
import asyncio
import os
from pymongo import MongoClient
from datetime import datetime
from simple_scraper import scrape


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
                    # Extract job config
                    url = job_data.get('url')
                    selectors = job_data.get('selectors', {})
                    
                    if not url or not selectors:
                        raise ValueError("Job missing url or selectors")
                    
                    # Run the scraper
                    asyncio.run(scrape(url, selectors))
                    
                    # Mark as completed
                    jobs_col.update_one(
                        {'_id': job_doc['_id']},
                        {'$set': {'status': 'completed', 'completed_at': datetime.utcnow()}}
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
