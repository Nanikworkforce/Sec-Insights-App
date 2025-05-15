# from .models.metric import FinancialMetric
from ..models.period import FinancialPeriod
# from .models.company import Company
from sec_app.models.company import Company
from sec_app.models.filing import Filing
from sec_app.models.mapping import MetricMapping
from sec_app.models.metric import FinancialMetric
from sec_app.api_client import fetch_filing_details
from django.utils.dateparse import parse_date
import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, date 
import re
import time
from dateutil import parser
from sec_app.api_client import fetch_filing_details
import io
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

def create_default_company():
    company, _ = Company.objects.get_or_create(
        ticker='DEFAULT',
        defaults={
            'name': 'Default Company',
            'cik': '0000000000'
        }
    )
    
    period_obj, _ = FinancialPeriod.objects.get_or_create(
        period='FY',
        company=company,
        defaults={
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 12, 31),
            'filing_date': date(2024, 12, 31)
        }
    )
    return period_obj

def initialize_metric_standards():
    """Initialize standard metrics - requires default company"""
    period_obj = create_default_company()
    
    FinancialMetric.objects.filter(period=period_obj).delete()
    
    standard_metrics = [
        { 
            'metric_name': 'Revenue',
            'xbrl_tag': 'us-gaap:Revenue',
            'unit': 'USD',
            'period': period_obj
        },
        {
            'metric_name': 'Net Income',
            'xbrl_tag': 'us-gaap:NetIncomeLoss',
            'unit': 'USD',
            'period': period_obj
        },
        {
            'metric_name': 'Operating Income',
            'xbrl_tag': 'us-gaap:OperatingIncomeLoss',
            'unit': 'USD',
            'period': period_obj
        },
        {
            'metric_name': 'Total Assets',
            'xbrl_tag': 'us-gaap:Assets',
            'unit': 'USD',
            'period': period_obj
        },
        {
            'metric_name': 'Total Liabilities',
            'xbrl_tag': 'us-gaap:Liabilities',
            'unit': 'USD',
            'period': period_obj
        },
    ]

    metrics_created = 0
    for metric in standard_metrics:
        FinancialMetric.objects.create(
            metric_name=metric['metric_name'],
            xbrl_tag=metric['xbrl_tag'],
            unit=metric['unit'],
            period=metric['period'],
            value=0.0
        )
        metrics_created += 1
    
    logger.info(f"Created {metrics_created} standard metrics")
    return metrics_created

def extract_xbrl_value(xbrl_data, tag_name):
    try:
        root = ET.fromstring(xbrl_data)
        
        namespaces = dict([node for _, node in ET.iterparse(io.BytesIO(xbrl_data), events=['start-ns'])])
        
        # Register the us-gaap namespace
        if 'us-gaap' not in namespaces:
            for prefix, uri in namespaces.items():
                if 'us-gaap' in uri.lower():
                    namespaces['us-gaap'] = uri
                    break
        
        # Log all available tags for debugging
        for elem in root.iter():
            if 'Revenue' in elem.tag or 'NetIncome' in elem.tag:  # Example condition
                logger.debug(f"Tag: {elem.tag}, Text: {elem.text}")

        # Create proper tag name with namespace
        tag_parts = tag_name.split(':')
        if len(tag_parts) == 2 and tag_parts[0] in namespaces:
            namespace = namespaces[tag_parts[0]]
            local_name = tag_parts[1]
            tag_with_namespace = f".//{{{namespace}}}{local_name}"
            
            # Find element with namespace
            element = root.find(tag_with_namespace)
            if element is not None:
                return float(element.text)
            
            # Try without namespace as fallback
            element = root.find(f".//{local_name}")
            if element is not None:
                return float(element.text)
                
        return None
    except Exception as e:
        logger.error(f"Error extracting XBRL value for tag {tag_name}: {str(e)}")
        return None

def deduplicate_metrics(company_ticker, period_obj):
    metrics = FinancialMetric.objects.filter(period=period_obj)
    
    # Group by metric name
    metric_groups = {}
    for metric in metrics:
        if metric.metric_name not in metric_groups:
            metric_groups[metric.metric_name] = []
        metric_groups[metric.metric_name].append(metric)
    
    for name, group in metric_groups.items():
        if len(group) > 1:
            sorted_group = sorted(group, key=lambda x: x.id)
            for metric in sorted_group[:-1]:
                logger.info(f"Removing duplicate {name} metric for {company_ticker}")
                metric.delete()

@sync_to_async
def save_financial_data_to_db(filings_data):
    ticker = filings_data.get('ticker')
    logger.info(f"Starting to save financial data for {ticker}")

    try:
        company, _ = Company.objects.update_or_create(
            ticker=ticker,
            defaults={
                'cik': filings_data.get('cik'),
                'name': filings_data.get('company_name', ticker),
            }
        )
        logger.info(f"Company updated: {company.ticker} ({company.name})")
    except Exception as e:
        logger.error(f"Error creating/updating company {ticker}: {e}")
        return 0, 0  
    filings_processed = 0
    metrics_created = 0
    for filing_data in filings_data.get('filings', []):
        filing_date, form_type = parse_filing_date(filing_data)
        if not filing_date or not form_type:
            logger.warning(f"Skipping filing due to missing fields: {filing_data}")
            continue
        try:
            filing, created = Filing.objects.update_or_create(
                company=company,
                filing_date=filing_date,
                form=form_type,
                defaults={
                    'accession_number': filing_data.get('accessionNumber', ''),
                    'fiscal_year_end': filing_data.get('fiscalYearEnd'),
                }
            )
            logger.info(f"Filing {'created' if created else 'updated'}: {form_type} from {filing_date}")
            filings_processed += 1
            period, _ = FinancialPeriod.objects.get_or_create(
                company=company,
                filing_date=filing_date,
                defaults={'period': filing_date.strftime('%Y')}
            )

            metrics_created += process_financial_metrics(filing_data, period, company)

        except Exception as e:
            logger.error(f"Error processing filing {filing_date}: {str(e)}")
            continue

    logger.info(f"Processed {filings_processed} filings and created {metrics_created} metrics")
    return filings_processed, metrics_created


def parse_filing_date(filing_data):
    if 'filedAt' in filing_data:
        return parse_date(filing_data.get('filedAt')), filing_data.get('formType')
    return (
        parse_date(filing_data.get('filing_date')) if isinstance(filing_data.get('filing_date'), str) else filing_data.get('filing_date'),
        filing_data.get('form')
    )


def process_financial_metrics(filing_data, period, company):
    metrics_created = 0

    if filing_data.get('data'):
        for metric_name, metric_data in filing_data['data'].items():
            value = metric_data.get('value', 0.0)
            logger.info(f"Processing metric: {metric_name}, Value: {value}, Period: {period}, Company: {company.ticker}")
            
            FinancialMetric.objects.update_or_create(
                period=period,
                company=company,
                metric_name=metric_name,
                defaults={
                    'value': value,
                    'xbrl_tag': metric_data.get('xbrl_tag', ''),
                    'unit': metric_data.get('unit', 'USD'),
                }
            )
            metrics_created += 1
    else:
        metrics_created += fetch_and_store_xbrl_data(company, filing_data, period)

    return metrics_created

def fetch_and_store_xbrl_data(company, filing_data, period):
    metrics_created = 0
    accession_number = filing_data.get('accessionNumber', '')

    if not accession_number:
        logger.warning(f"No accession number found for {company.ticker}, skipping XBRL fetch.")
        return metrics_created

    try:
        # Add delay to avoid rate limiting
        time.sleep(0.1)
        
        filing_details = fetch_filing_details(company.cik, accession_number)
        if not filing_details:
            logger.warning(f"No filing details found for {company.ticker} filing {accession_number}")
            return metrics_created

        # Try to find the XBRL instance document
        xbrl_files = [f for f in filing_details.get('directory', {}).get('item', [])
                      if f.get('name', '').endswith('.xml') and not any(suffix in f.get('name', '') for suffix in ['_cal', '_def', '_lab', '_pre', 'FilingSummary'])]
        
        if not xbrl_files:
            logger.warning(f"No XBRL instance files found for {company.ticker} filing {accession_number}")
            return metrics_created

        # Get the first XBRL instance file
        xbrl_file = xbrl_files[0]
        xbrl_url = f"https://www.sec.gov/Archives/edgar/data/{int(company.cik)}/{accession_number}/{xbrl_file['name']}"
        
        headers = {
            'User-Agent': 'Nanik paul@nanikworkforce.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        response = requests.get(xbrl_url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch XBRL data: {response.status_code}")
            return metrics_created

        xbrl_data = response.content
        logger.info(f"Fetched XBRL data from {xbrl_url}")

        # Log a portion of the XBRL data for debugging
        logger.debug(f"XBRL data snippet: {xbrl_data[:500]}")

        metric_mappings = [
            {'name': 'Revenue', 'xbrl_tag': 'us-gaap:SalesRevenueNet'},
            {'name': 'Profit', 'xbrl_tag': 'us-gaap:NetIncomeLoss'},
            {'name': 'Total Assets', 'xbrl_tag': 'us-gaap:Assets'}
        ]

        for metric_info in metric_mappings:
            value = extract_xbrl_value(xbrl_data, metric_info['xbrl_tag'])
            if value is not None:
                FinancialMetric.objects.update_or_create(
                    period=period,
                    company=company,
                    metric_name=metric_info['name'],
                    defaults={
                        'value': value,
                        'xbrl_tag': metric_info['xbrl_tag'],
                        'unit': 'USD',
                    }
                )
                metrics_created += 1
                logger.info(f"Stored metric: {metric_info['name']} ({value} USD)")
            else:
                logger.warning(f"Metric {metric_info['name']} not found in XBRL data")

    except Exception as e:
        logger.error(f"Error fetching or processing XBRL data for {company.ticker}: {str(e)}")

    return metrics_created
