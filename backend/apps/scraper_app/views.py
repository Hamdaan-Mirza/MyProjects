from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from pymongo import MongoClient
import os
from .tasks import enqueue_job


mongo = MongoClient(os.getenv('MONGO_URI', settings.MONGO_URI))
COL = mongo.scraper_db.listings


@api_view(['GET'])
def list_listings(request):
	"""Return recent listings with additional fields used by the UI."""
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
			'first_seen': d.get('first_seen'),
			'scraped_at': d.get('scraped_at'),
			'source': d.get('source'),
			'job_query': d.get('job_query'),
		})
	return Response(items)


@api_view(['POST'])
def run_job(request):
	# Trigger scraper job: validate and enqueue to Celery (stored in Mongo jobs collection)
	job = request.data.get('job')
	if not job:
		return Response({'status': 'error', 'detail': 'missing job payload'}, status=400)

	task = enqueue_job.delay(job)
	return Response({'status': 'scheduled', 'task_id': getattr(task, 'id', None)})


@api_view(['GET'])
def list_jobs(request):
	"""Return recent jobs from the jobs collection for Job History panel."""
	client = mongo
	jcol = client.scraper_db.jobs
	cursor = jcol.find({}).sort('created_at', -1).limit(100)
	items = []
	for d in cursor:
		job = d.get('job') or {}
		items.append({
			'task_id': str(d.get('_id')),
			'status': d.get('status', 'pending'),
			'created_at': d.get('created_at'),
			# Flatten common job fields
			'type': job.get('type'),
			'query': job.get('query'),
			'limit': job.get('limit'),
			'count': d.get('count'),
			'started_at': d.get('started_at'),
			'completed_at': d.get('completed_at'),
			'failed_at': d.get('failed_at'),
		})
	return Response(items)