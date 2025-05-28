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
    # Extract time range patterns
    time_range_match = re.search(r"(?:last|past)\s+(\d+)\s*(?:year|years|yr|yrs)", text, re.I)
    year_range_match = re.search(r"(\d{4})\s*(?:to|-)\s*(\d{4})", text, re.I)
    
    # First try to match ticker format (2-5 uppercase letters)
    ticker_match = re.search(r"\b([A-Z]{2,5})\b", text)
    if ticker_match:
        ticker = ticker_match.group(1)
        from sec_app.models.company import Company
        if not Company.objects.filter(ticker__iexact=ticker).exists():
            return {
                "invalid_company": ticker,
                "year": re.search(r"\b(20\d{2})\b", text).group(0) if re.search(r"\b(20\d{2})\b", text) else None,
                "metric": extract_metric(text),
                "time_range": time_range_match.group(1) if time_range_match else None,
                "year_range": (year_range_match.group(1), year_range_match.group(2)) if year_range_match else None
            }
        return {
            "company": ticker,
            "year": re.search(r"\b(20\d{2})\b", text).group(0) if re.search(r"\b(20\d{2})\b", text) else None,
            "metric": extract_metric(text),
            "time_range": time_range_match.group(1) if time_range_match else None,
            "year_range": (year_range_match.group(1), year_range_match.group(2)) if year_range_match else None
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
    # Try to match "the X of Y" or "the X for Y"
    match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:of|for)\s+[A-Z]{2,5}", text, re.I)
    if match:
        return to_camel_case(match.group(1).strip())

    # Try to match "the X of Y from YEAR to YEAR"
    match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:of|for)\s+[A-Z]{2,5}.*?(?:from|between)?\s*\d{4}.*?\d{4}", text, re.I)
    if match:
        return to_camel_case(match.group(1).strip())

    # Try to match "the X in the last N years"
    match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:in|over)?\s*(?:the)?\s*last\s*\d+\s*years?", text, re.I)
    if match:
        return to_camel_case(match.group(1).strip())

    # Try to match "what is my X"
    match = re.search(r"what is (?:my|the) ([\w\s\-]+?)(?:\s+in|\s*$)", text, re.I)
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

    # Only annual periods
    filters["period__period__regex"] = r"^\d{4}$"

    # Handle time ranges
    current_year = 2024  # Or dynamically get the latest year
    if context.get("time_range"):
        years = int(context["time_range"])
        start_year = current_year - years + 1
        filters["period__start_date__year__gte"] = start_year
        filters["period__start_date__year__lte"] = current_year
    elif context.get("year_range"):
        start_year, end_year = context["year_range"]
        filters["period__start_date__year__gte"] = int(start_year)
        filters["period__start_date__year__lte"] = int(end_year)
    elif context.get("year"):
        filters["period__start_date__year"] = context["year"]

    try:
        start = time.time()
        qs = FinancialMetric.objects.filter(**filters)\
            .select_related('company', 'period')\
            .only('value', 'metric_name', 'company__ticker', 'period__start_date', 'period__period')\
            .order_by('-period__start_date')

        if not qs.exists():
            return f"No data found for the specified period."

        # If it's a time range query, return all values
        if context.get("time_range") or context.get("year_range"):
            data = list(qs)
            # Group by year, take the latest value for each year
            year_to_metric = {}
            for d in data:
                year = d.period.start_date.year
                # If multiple entries for the same year, keep the latest (qs is ordered by -period__start_date)
                if year not in year_to_metric:
                    year_to_metric[year] = d

            # Sort years descending (latest first)
            sorted_years = sorted(year_to_metric.keys(), reverse=True)
            # Adjust the scaling here based on your database!
            values = [f"{year}: ${year_to_metric[year].value:.2f}B" for year in sorted_years]

            if context.get("year_range"):
                period_str = f"{context['year_range'][0]} to {context['year_range'][1]}"
            else:
                period_str = f"last {context['time_range']} years ({current_year-int(context['time_range'])+1} to {current_year})"

            return f"{data[0].company.ticker} {data[0].metric_name} for {period_str}:\n" + "\n".join(values)
        
        # Single year query (existing logic)
        data = qs.first()
        response_year = context.get('year') or data.period.start_date.year
        return f"{data.company.ticker} {data.metric_name} for {response_year} is ${data.value:.2f}B"

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
