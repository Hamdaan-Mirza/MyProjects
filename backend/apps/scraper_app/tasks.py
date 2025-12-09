from celery import shared_task
from pymongo import MongoClient
import os
import json
import datetime


@shared_task
def enqueue_job(job_payload):
	"""Store a job document in MongoDB for worker to pick up.

	job_payload can be a dict or JSON string.
	"""
	if isinstance(job_payload, str):
		try:
			job = json.loads(job_payload)
		except Exception:
			job = {'path': job_payload}
	else:
		job = job_payload or {}

	mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/scraper_db')
	client = MongoClient(mongo_uri)
	jobs = client.scraper_db.jobs
	doc = {
		'job': job,
		'status': 'pending',
		'created_at': datetime.datetime.utcnow(),
	}
	res = jobs.insert_one(doc)
	return str(res.inserted_id)