import requests
from django.conf import settings
import logging
import time
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# SEC API endpoints
BASE_URL = "https://data.sec.gov/api" 
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Headers for SEC API requests
HEADERS = {
    'User-Agent': 'Nanik paul@nanikworkforce.com',  # Make sure this is a valid email
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

CIK_CACHE = {}
#stocks_perf
cache_file = os.path.join(os.path.dirname(__file__), 'data', 'cik_cache.json')
if os.path.exists(cache_file):
    try:
        with open(cache_file, 'r') as f:
            loaded_cache = json.load(f)
            CIK_CACHE.update(loaded_cache)
        logger.info(f"Loaded {len(loaded_cache)} CIK entries from cache file")
    except Exception as e:
        logger.error(f"Error loading CIK cache: {str(e)}")

def get_cik_from_ticker(ticker):
    """Get CIK number from ticker symbol"""
    ticker = ticker.upper()
    
    # Check cache first
    if ticker in CIK_CACHE:
        return CIK_CACHE[ticker]
    
    # Try direct lookup first (more reliable)
    try:
        direct_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}&owner=exclude&action=getcompany&Find=Search"
        response = requests.get(direct_url, headers={
            'User-Agent': 'Nanik paul@nanikworkforce.com',
        })
        
        if response.status_code == 200:
            # Look for CIK in the response text
            import re
            cik_match = re.search(r'CIK=(\d+)', response.text)
            if cik_match:
                cik = cik_match.group(1).zfill(10)
                CIK_CACHE[ticker] = cik
                logger.info(f"Found CIK for {ticker} via direct lookup: {cik}")
                return cik
    except Exception as e:
        logger.error(f"Error in direct CIK lookup for {ticker}: {str(e)}")
    
    common_ciks = {
        'AAPL': '0000320193',
        'MSFT': '0000789019',
        'GOOGL': '0001652044',
        'AMZN': '0001018724',
        'META': '0001326801', 
        'TSLA': '0001318605',
        'NVDA': '0001045810',
        'JPM': '0000019617',
        'JNJ': '0000200406',
        'V': '0001403161',
    }
    
    if ticker in common_ciks:
        cik = common_ciks[ticker]
        CIK_CACHE[ticker] = cik
        logger.info(f"Found CIK for {ticker} from hardcoded values: {cik}")
        return cik
    
    try:
        response = requests.get(COMPANY_TICKERS_URL, headers=HEADERS)
        if response.status_code == 200:
            companies = response.json()
            
            # The SEC JSON structure has numeric keys with company data as values
            for _, company_data in companies.items():
                if company_data.get('ticker') == ticker:
                    # Format CIK with leading zeros to make it 10 digits
                    cik = str(company_data.get('cik_str')).zfill(10)
                    CIK_CACHE[ticker] = cik
                    logger.info(f"Found CIK for {ticker} from company_tickers.json: {cik}")
                    return cik
        else:
            logger.error(f"Failed to fetch company tickers: {response.status_code}")
    except Exception as e:
        logger.error(f"Error accessing company_tickers.json: {str(e)}")
    
    # If all methods fail, return None
    logger.warning(f"Could not find CIK for ticker {ticker} using any method")
    return None

def fetch_financial_data(ticker, verbose=False):

    if verbose:
        print(f"Requesting 10-K filings for {ticker}")
    
    cik = get_cik_from_ticker(ticker)
    if not cik:
        if verbose:
            print(f"Could not find CIK for {ticker}")
        return None
    
    print(f"Found CIK for {ticker}: {cik}")
    
    cik_int = int(cik)
    cik_formatted = str(cik_int)
    cik_padded = cik_formatted.zfill(10)
    
    urls_to_try = [
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/index.json",
        f"https://data.sec.gov/submissions/CIK{cik_padded}.json",
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json",
        f"https://data.sec.gov/submissions/CIK{cik_formatted}.json",
        f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_formatted}&type=10-K&dateb=&owner=exclude&count=10&output=atom"
    ]
    
    headers = {
        'User-Agent': 'Nanik paul@nanikworkforce.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    
    if verbose:
        print(f"Using headers: {headers}")
    
    filings_data = None
    
    for url in urls_to_try:
        print(f"Trying URL: {url}")
        
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            # Adjust headers based on the URL
            if 'www.sec.gov' in url:
                current_headers = {
                    'User-Agent': 'Nanik paul@nanikworkforce.com',
                    'Accept-Encoding': 'gzip, deflate',
                    'Host': 'www.sec.gov'
                }
            else:
                current_headers = headers
            
            response = requests.get(url, headers=current_headers, timeout=15)
            
            if response.status_code == 200:
                print(f"Success! Got response from {url}")
                
                # Special handling for atom feed
                if 'output=atom' in url:
                    # Parse XML response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    filings_data = {
                        'ticker': ticker,
                        'cik': cik,
                        'company_name': '',
                        'filings': []
                    }
                    
                    # Extract entries (filings)
                    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                        title = entry.find('.//{http://www.w3.org/2005/Atom}title').text
                        if '10-K' in title:
                            filing_date = entry.find('.//{http://www.w3.org/2005/Atom}updated').text.split('T')[0]
                            filings_data['filings'].append({
                                'form': '10-K',
                                'filing_date': filing_date,
                                'accession_number': '',
                                'fiscal_year_end': '',
                                'data': {}
                            })
                    
                    if filings_data['filings']:
                        print(f"Successfully extracted {len(filings_data['filings'])} 10-K filings from atom feed")
                        break
                    else:
                        filings_data = None
                    continue
                
                try:
                    data = response.json()
                    
                    # Process the data to extract 10-K filings
                    filings_data = {
                        'ticker': ticker,
                        'cik': cik,
                        'company_name': data.get('name', ''),
                        'filings': []
                    }
                    
                    # Extract filings based on the URL format/response structure
                    if 'submissions' in url:
                        # Handle submissions endpoint format
                        recent_filings = data.get('filings', {}).get('recent', {})
                        for i, form in enumerate(recent_filings.get('form', [])):
                            if form == '10-K':
                                filing_date = recent_filings.get('filingDate', [])[i]
                                # Format accession number properly by removing dashes
                                raw_accession = recent_filings.get('accessionNumber', [])[i]
                                accession_number = raw_accession.replace('-', '') if raw_accession else ''
                                
                                filings_data['filings'].append({
                                    'form': form,
                                    'filing_date': filing_date,
                                    'accessionNumber': accession_number,  # Changed from accession_number to match usage
                                    'fiscal_year_end': recent_filings.get('fiscalYearEnd', [])[i] if i < len(recent_filings.get('fiscalYearEnd', [])) else None,
                                    'data': {}
                                })
                    
                    elif 'companyfacts' in url:
                        # Handle companyfacts endpoint format
                        facts = data.get('facts', {})
                        us_gaap = facts.get('us-gaap', {})
                        
                        # Extract filing dates from the facts
                        filing_dates = set()
                        for metric, metric_data in us_gaap.items():
                            for unit, unit_data in metric_data.get('units', {}).items():
                                for entry in unit_data:
                                    if entry.get('form') == '10-K':
                                        filing_dates.add(entry.get('filed'))
                        
                        # Create filing entries
                        for filing_date in sorted(filing_dates, reverse=True):
                            filings_data['filings'].append({
                                'form': '10-K',
                                'filing_date': filing_date,
                                'accession_number': None,  # Not available in this format
                                'fiscal_year_end': None,   # Not available in this format
                                'data': {}
                            })
                        
                        # Populate financial metrics for each filing
                        for metric, metric_data in us_gaap.items():
                            for unit, unit_data in metric_data.get('units', {}).items():
                                for entry in unit_data:
                                    if entry.get('form') == '10-K':
                                        filing_date = entry.get('filed')
                                        
                                        # Find the corresponding filing
                                        for filing in filings_data['filings']:
                                            if filing['filing_date'] == filing_date:
                                                filing['data'][metric] = {
                                                    'value': entry.get('val'),
                                                    'unit': unit,
                                                    'end_date': entry.get('end'),
                                                    'start_date': entry.get('start')
                                                }
                    
                    elif 'Archives/edgar' in url:
                        # Handle index.json format
                        for item in data.get('directory', {}).get('item', []):
                            if '10-K' in item.get('name', ''):
                                filing_date = item.get('last-modified', '').split('T')[0]
                                filings_data['filings'].append({
                                    'form': '10-K',
                                    'filing_date': filing_date,
                                    'accession_number': item.get('name', ''),
                                    'fiscal_year_end': None,
                                    'data': {}
                                })
                    
                    if filings_data['filings']:
                        print(f"Successfully extracted {len(filings_data['filings'])} 10-K filings from {url}")
                        break
                    else:
                        print(f"No 10-K filings found in the response from {url}")
                        filings_data = None
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON from {url}: {str(e)}")
                    print(f"Response content: {response.text[:200]}...")
            else:
                print(f"Failed to fetch from {url}: {response.status_code}")
        except Exception as e:
            print(f"Error accessing {url}: {str(e)}")
    
    if not filings_data or not filings_data['filings']:
        print(f"All URL formats failed for {ticker}")
        return None
    
    return filings_data

def fetch_company_facts(ticker):
    try:
        api_key = settings.SEC_API_KEY
        
        if not api_key:
            logger.error("SEC_API_KEY is not set in settings")
            return None
            
        api_url = "https://api.sec-api.io/"
        
        params = {
            "token": api_key,
            "query": f'ticker:{ticker} AND formType:"10-K"',
            "from": 0,
            "size": 1,
            "sort": '[{"filedAt":{"order":"desc"}}]'
        }

        logger.info(f"Requesting company facts: {api_url} with params: {params}")
        
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            logger.debug(f"Response content: {response.text[:200]}...")
            return response.json()
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error fetching company facts: {str(e)}")
        return None

def fetch_financial_data_alternative(ticker):
    """
    Alternative method to fetch financial data using Financial Modeling Prep API
    """
    # You would need to set this in your settings.py
    api_key = getattr(settings, 'FMP_API_KEY', None)
    
    if not api_key:
        print("FMP_API_KEY not set in settings")
        return None
    
    url = f"https://financialmodelingprep.com/api/v3/sec_filings/{ticker}?type=10-K&limit=10&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data:
                print(f"No filings found for {ticker}")
                return None
            
            filings_data = {
                'ticker': ticker,
                'cik': data[0].get('cik', ''),
                'company_name': data[0].get('companyName', ''),
                'filings': []
            }
            
            for filing in data:
                if filing.get('type') == '10-K':
                    filings_data['filings'].append({
                        'form': '10-K',
                        'filing_date': filing.get('fillingDate', ''),
                        'accession_number': filing.get('accessionNumber', ''),
                        'fiscal_year_end': '',
                        'data': {}
                    })
            
            return filings_data
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

def fetch_filing_details(cik, accession_number):
    formatted_accession = accession_number.replace('-', '')     
    cik_int = int(cik)
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{formatted_accession}/index.json"
    
    headers = {
        'User-Agent': 'Nanik paul@nanikworkforce.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch filing details: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching filing details: {str(e)}")
        return None
