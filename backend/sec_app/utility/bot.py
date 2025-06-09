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

def is_news_query(text):
    # Accepts queries like "what is the latest news of meta", "show me news for AMZN", etc.
    news_patterns = [
        r"\b(latest|recent)?\s*news\s*(of|for|about)?\s*([A-Za-z0-9\-\:\. ]+)",  # e.g. latest news of meta:AM
        r"\bshow me news\s*(of|for|about)?\s*([A-Za-z0-9\-\:\. ]+)",
        r"\bnews\s*(of|for|about)?\s*([A-Za-z0-9\-\:\. ]+)",
    ]
    for pat in news_patterns:
        m = re.search(pat, text, re.I)
        if m:
            # Try to extract the company/ticker part
            # Try group 3, then group 2
            company = m.group(3) if m.lastindex and m.lastindex >= 3 and m.group(3) else m.group(2)
            if company:
                # Remove possible "of"/"for"/"about" at the start
                company = company.strip()
                # Remove trailing punctuation
                company = re.sub(r"[^\w\:\-\. ]+$", "", company)
                # Remove "stock" if present
                company = re.sub(r"\bstock\b", "", company, flags=re.I).strip()
                return company
    return None

def extract_keywords(text):
    # News query detection
    news_company = is_news_query(text)
    if news_company:
        return {
            "news_company": news_company
        }

    # Extract time range patterns - make pattern more flexible
    time_range_match = re.search(r"(?:in |over |during |for )?(?:the )?(?:last|past)\s+(\d+)\s*(?:year|years|yr|yrs)", text, re.I)
    year_range_match = re.search(r"(\d{4})\s*(?:to|-)\s*(\d{4})", text, re.I)
    
    # Extract growth intent before any use
    growth_match = re.search(r"\bgrowth\b", text, re.I)

    # Extract company from possessive or "of/for" forms
    company = None
    possessive_match = re.search(r"\b([A-Z]{2,5})'s\b", text)
    if possessive_match:
        company = possessive_match.group(1)
    else:
        of_for_match = re.search(r"(?:of|for)\s+([A-Z]{2,5})\b", text, re.I)
        if of_for_match:
            company = of_for_match.group(1)
    if not company:
        ticker_match = re.search(r"\b([A-Z]{2,5})\b", text)
        if ticker_match:
            company = ticker_match.group(1)

    if company:
        from sec_app.models.company import Company
        if not Company.objects.filter(ticker__iexact=company).exists():
            return {
                "invalid_company": company,
                "year": re.search(r"\b(20\d{2})\b", text).group(0) if re.search(r"\b(20\d{2})\b", text) else None,
                "metric": extract_metric(text),
                "time_range": time_range_match.group(1) if time_range_match else None,
                "year_range": (year_range_match.group(1), year_range_match.group(2)) if year_range_match else None,
                "growth": bool(growth_match)
            }

    # If no company found, just return None for company (no hardcoded fallback)
    year_match = re.search(r"\b(20\d{2})\b", text)
    return {
        "company": company,
        "year": year_match.group(0) if year_match else None,
        "metric": extract_metric(text),
        "time_range": time_range_match.group(1) if time_range_match else None,
        "year_range": (year_range_match.group(1), year_range_match.group(2)) if year_range_match else None,
        "growth": bool(growth_match)
    }

def to_camel_case(s):
    """Convert 'net income' -> 'netIncome'"""
    # Remove any extra spaces and split
    words = s.strip().lower().split()
    # Capitalize all words after first one and join
    return words[0] + ''.join(word.capitalize() for word in words[1:])

def extract_metric(text):
    metric = None
    
    # Pattern: "growth in METRIC in the last X years" or "from YEAR to YEAR"
    match = re.search(r"growth\s+(?:in|of|for)\s+([\w\s\-]+?)(?:\s+(?:in|over|during|for|from)\s|$)", text, re.I)
    if match:
        metric = match.group(1)

    # Pattern: "METRIC growth in the last X years" or "from YEAR to YEAR"
    if not metric:
        match = re.search(r"([\w\s\-]+?)\s+growth(?:\s+(?:in|over|during|for|from)\s|$)", text, re.I)
        if match:
            metric = match.group(1)

    # Pattern: "COMPANY's METRIC growth"
    if not metric:
        match = re.search(r"[A-Z]{2,5}'s\s+([\w\s\-]+?)\s*growth", text, re.I)
        if match:
            metric = match.group(1)

    # Pattern: "growth in METRIC" or "growth of METRIC"
    if not metric:
        match = re.search(r"growth\s+(?:in|of|for)\s+([\w\s\-]+)", text, re.I)
        if match:
            metric = match.group(1)

    # Pattern: "the METRIC growth of COMPANY"
    if not metric:
        match = re.search(r"(?:the\s+)?([\w\s\-]+?)\s+growth\s+(?:of|for)\s+[A-Z]{2,5}", text, re.I)
        if match:
            metric = match.group(1)

    # Existing patterns...
    if not metric:
        match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:of|for)\s+[A-Z]{2,5}", text, re.I)
        if match:
            metric = match.group(1)

    # Try to match "the X of Y from YEAR to YEAR"
    if not metric:
        match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:of|for)\s+[A-Z]{2,5}.*?(?:from|between)?\s*\d{4}.*?\d{4}", text, re.I)
        if match:
            metric = match.group(1)

    # Try to match "the X in the last N years"
    if not metric:
        match = re.search(r"(?:what is|show|give|display|provide)?\s*(?:the|my)?\s*([\w\s\-]+?)\s*(?:in|over)?\s*(?:the)?\s*last\s*\d+\s*years?", text, re.I)
        if match:
            metric = match.group(1)

    # Try to match "what is my X"
    if not metric:
        match = re.search(r"what is (?:my|the) ([\w\s\-]+?)(?:\s+in|\s*$)", text, re.I)
        if match:
            metric = match.group(1)

    # fallback: phrase after "of"/"for" and before "in"/end
    if not metric:
        match = re.search(r"(?:of|for)\s+([a-zA-Z0-9 \-\_]+?)(?:\s+in\b|$)", text, re.I)
        if match:
            metric = match.group(1)

    if not metric:
        # Final attempt: look for word "growth" and take what's before it
        match = re.search(r"([\w\s\-]+?)\s*growth\b", text, re.I)
        if match:
            metric = match.group(1)

    if metric:
        # Always strip 'growth' from the end and clean up
        metric = re.sub(r"\s*growth\b", "", metric, flags=re.I).strip()
        return to_camel_case(metric)

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
    # News query support
    if context.get("news_company"):
        return fetch_google_news(context["news_company"])

    # Growth query support
    if context.get("growth"):
        company = context.get("company")
        metric_name = context.get("metric_name")
        if not company or not metric_name:
            return "Please specify a company and metric to calculate growth."
        # Only annual periods
        filters = {
            "company__ticker__iexact": company.upper(),
            "metric_name__iexact": metric_name,
            "period__period__regex": r"^\d{4}$"
        }
        qs = FinancialMetric.objects.filter(**filters).select_related('period').order_by('-period__start_date')
        if qs.count() < 2:
            return f"Not enough data to calculate {metric_name} growth for {company}."
        latest = qs[0]
        prev = qs[1]
        try:
            growth = ((latest.value - prev.value) / prev.value) * 100 if prev.value else 0
            return (
                f"{latest.company.ticker} {latest.metric_name} grew by {growth:.2f}% "
                f"in the last year ({prev.period.start_date.year} to {latest.period.start_date.year})"
            )
        except Exception:
            return f"Could not calculate growth for {company} {metric_name}."

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

        # If it's a time range query, return only the total (not all values)
        if context.get("time_range") or context.get("year_range"):
            data = list(qs)
            year_to_metric = {}
            for d in data:
                year = d.period.start_date.year
                if year not in year_to_metric:
                    year_to_metric[year] = d

            sorted_years = sorted(year_to_metric.keys(), reverse=True)
            total = sum([year_to_metric[year].value for year in sorted_years])

            if context.get("year_range"):
                period_str = f"{context['year_range'][0]} to {context['year_range'][1]}"
            else:
                period_str = f"the last {context['time_range']} years"

            # Compose the response with only the total
            return (
                f"{data[0].company.ticker}'s {data[0].metric_name.capitalize()} for {period_str} is ${total/1e9:.1f}B"
            )
        
        # Single year query (existing logic)
        data = qs.first()
        response_year = context.get('year') or data.period.start_date.year
        return f"{data.company.ticker} {data.metric_name} for {response_year} is ${data.value/1e9:.1f}B"

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
    if payload.get("news_company"):
        parts.append(f"the latest news for {payload['news_company']}")

    if parts:
        return f"Based on your previous selections, you are trying to understand {' '.join(parts)}."
    return "You're exploring business performance insights."
