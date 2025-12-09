from celery import shared_task
import subprocess


@shared_task
def run_scraper_job(job_config_path):
# Example: call worker script with job path
subprocess.run(['python', '/worker/scraper/simple_scraper.py', job_config_path], check=True)