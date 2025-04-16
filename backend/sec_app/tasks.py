from celery import shared_task
from django.core.management import call_command
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_sec_filings():
    try:
        logger.info("Starting scheduled SEC filings update")
        call_command('update_sec_filings', '--days-back=90', '--batch-size=10')
        logger.info("Completed scheduled SEC filings update")
    except Exception as e:
        logger.error(f"Error in scheduled SEC filings update: {str(e)}") 