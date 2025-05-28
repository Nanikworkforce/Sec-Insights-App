import re
from django.utils.translation import gettext_lazy as _
import logging
from sec_app.models.metric import FinancialMetric  
from sec_app.models.period import FinancialPeriod
from django.db import models
import feedparser 
import time

logger = logging.getLogger(__name__)

def fetch_google_news(company):
    query = company.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={query}+stock"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return f"No recent news found for {company}."

    articles = feed.entries[:5]
    links = [f"- [{entry.title}]({entry.link})" for entry in articles]
    return f"📰 Here are the latest news articles related to **{company}**:\n\n" + "\n".join(links)


def extract_keywords(text):
    # First try to match ticker format (2-5 uppercase letters)
    ticker_match = re.search(r"\b([A-Z]{2,5})\b", text)
    if ticker_match:
        ticker = ticker_match.group(1)
        from sec_app.models.company import Company
        if not Company.objects.filter(ticker__iexact=ticker).exists():
            return {
                "invalid_company": ticker,
                "year": re.search(r"\b(20\d{2})\b", text).group(0) if re.search(r"\b(20\d{2})\b", text) else None,
                "metric": extract_metric(text)
            }
        return {
            "company": ticker,
            "year": re.search(r"\b(20\d{2})\b", text).group(0) if re.search(r"\b(20\d{2})\b", text) else None,
            "metric": extract_metric(text)
        }

    # Fallback to company name matching
    company_match = re.search(r"\b(Apple|Tesla|Amazon|Meta|Google|Acadian Asset Management|AAON)\b", text, re.I)
    year_match = re.search(r"\b(20\d{2})\b", text)
    return {
        "company": company_match.group(0) if company_match else None,
        "year": year_match.group(0) if year_match else None,
        "metric": extract_metric(text)
    }

def to_camel_case(s):
    """Convert 'net income' -> 'netIncome'"""
    # Remove any extra spaces and split
    words = s.strip().lower().split()
    # Capitalize all words after first one and join
    return words[0] + ''.join(word.capitalize() for word in words[1:])

def extract_metric(text):
    # Handle simple "what is my X" pattern first
    simple_match = re.search(r"what is (?:my|the) ([\w\s\-]+?)(?:\s+in|\s*$)", text, re.I)
    if simple_match:
        return to_camel_case(simple_match.group(1).strip())

    # Prefer metric between "is the" and "of"/"for" and ticker
    match = re.search(r"is the ([\w\s\-]+?) (?:of|for) [A-Z]{2,5}", text, re.I)
    if match:
        return to_camel_case(match.group(1).strip())

    # fallback: phrase after "of"/"for" and before "in"/end
    match = re.search(r"(?:of|for)\s+([a-zA-Z0-9 \-\_]+?)(?:\s+in\b|$)", text, re.I)
    if match:
        return to_camel_case(match.group(1).strip())

    return None

def is_introspective_question(text):
    introspective_patterns = [
        r"who am i",
        r"what am i doing",
        r"what.*trying to do",
        r"what.*going on",
    ]
    return any(re.search(p, text, re.I) for p in introspective_patterns)

def query_data_from_db(context):
    filters = {}
    if context.get("company"):
        filters["company__ticker__iexact"] = context["company"].upper()
    elif context.get("companies"):
        filters["company__ticker__in"] = context["companies"]
    
    metric_name = context.get("metric_name")
    if metric_name:
        if isinstance(metric_name, list):
            filters["metric_name__in"] = metric_name
        else:
            filters["metric_name__iexact"] = metric_name

    year = context.get("year")
    tried_year = False
    if year:
        filters["period__start_date__year"] = year
        tried_year = True

    try:
        start = time.time()
        qs = FinancialMetric.objects.filter(**filters)\
            .select_related('company', 'period')\
            .only('value', 'metric_name', 'company__ticker', 'period__start_date')\
            .order_by('-period__start_date')

        duration = time.time() - start
        print(f"FinancialMetric query time: {duration:.4f} seconds")
        print(f"Query filters: {filters}")

        # If no results and we tried a specific year, fallback to latest year
        if not qs.exists() and tried_year:
            print("No data found for the specified year, trying to find the latest available year.")
            filters.pop("period__start_date__year", None)
            latest = FinancialMetric.objects.filter(**filters)\
                .order_by('-period__start_date').first()
            if latest:
                filters["period__start_date__year"] = latest.period.start_date.year
                qs = FinancialMetric.objects.filter(**filters)\
                    .select_related('company', 'period')\
                    .only('value', 'metric_name', 'company__ticker', 'period__start_date')\
                    .order_by('-period__start_date')

        if not qs.exists():
            print(f"No data found with filters: {filters}")
            return f"No data found for {context.get('year', 'the latest period')}."

        data = qs.first()
        response_year = context.get('year') or data.period.start_date.year
        return f"{data.company.ticker} {data.metric_name} for {response_year} is {data.value}."
    except Exception as e:
        logger.error(f"Error in query_data_from_db: {str(e)}")
        return "Sorry, I couldn't find data based on your query."

def describe_payload_intent(payload):
    parts = []
    if payload.get("company"):
        parts.append(f"the performance of company {payload['company']}")
    if payload.get("metric_name"):
        parts.append(f"the metric '{payload['metric_name']}'")
    if payload.get("year"):
        parts.append(f"in {payload['year']}")

    if parts:
        return f"Based on your previous selections, you are trying to understand {' '.join(parts)}."
    return "You're exploring business performance insights."
