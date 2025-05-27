import re
from django.utils.translation import gettext_lazy as _
import logging
from sec_app.models.metric import FinancialMetric  
from sec_app.models.period import FinancialPeriod
from django.db import models
import feedparser 
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
    company_match = re.search(r"\b(?:Apple|Tesla|Amazon|Meta|Google)\b", text, re.I)
    year_match = re.search(r"\b(20\d{2})\b", text)
    metric_match = re.search(r"\b(revenue|net income|eps|assets|liabilities)\b", text, re.I)

    return {
        "company": company_match.group(0) if company_match else None,
        "year": year_match.group(0) if year_match else None,
        "metric": metric_match.group(0).lower() if metric_match else None,
    }

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
        filters["company__name__iexact"] = context["company"]
    if context.get("metric_name"):
        filters["metric_name__iexact"] = context["metric_name"]
    if context.get("period"):
        filters["period"] = context["period"]

    qs = FinancialMetric.objects.filter(**filters)
    if not qs.exists():
        return "Sorry, I couldn't find data based on your query."

    data = qs.first()
    return f"{data.company.name} had a {data.metric_name} of {data.value} in {data.period}."

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
