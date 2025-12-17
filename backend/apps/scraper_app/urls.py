from django.urls import path
from . import views


urlpatterns = [
path('listings/', views.list_listings, name='list_listings'),
path('run-job/', views.run_job, name='run_job'),
	path('jobs/', views.list_jobs, name='list_jobs'),
]