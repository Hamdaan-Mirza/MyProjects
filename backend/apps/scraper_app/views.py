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