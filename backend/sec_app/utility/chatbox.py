import re
from django.utils.translation import gettext_lazy as _
import logging
from sec_app.models.metric import FinancialMetric  
from sec_app.models.period import FinancialPeriod
from django.db import models
import feedparser 
logger = logging.getLogger(__name__)

def normalize_metric_name(metric: str) -> str:
    normalized = re.sub(r'(?<!^)(?=[A-Z])', ' ', metric).lower()
    return normalized

def fetch_google_news(company):
    query = company.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={query}+stock"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return f"No recent news found for {company}."

    articles = feed.entries[:5]
    links = [f"- [{entry.title}]({entry.link})" for entry in articles]
    return f"📰 Here are the latest news articles related to **{company}**:\n\n" + "\n".join(links)


def answer_question(question: str, chart_context: dict, chart_data: list) -> str:
    try:
        chart_type = chart_context.get("chart_type", "line")
        company = chart_context.get("company", "")
        metrics = chart_context.get("metrics", [])
        selected_peers = chart_context.get("selected_peers", [])
        question_lower = question.lower()

        if "news" in question or "latest news" in question:
            return fetch_google_news(company)
        else:
            "I'm still learning how to answer that question. Try rephrasing or ask about metrics or trends."

        if "stock" in question and ("perform" in question or "price" in question):
            return f"📈 Here is the Google Finance page for {company}:\nhttps://www.google.com/finance/quote/{company}:NASDAQ"

        if any(keyword in question for keyword in ["how is market perceiving", "how is the market reacting", "market sentiment", "perceiving us", "perceiving our stock"]):
            return f"📰 Here's how the market is perceiving **{company}**:\n" + get_bloomberg_sentiment_news(company)

        if "what are the trends of selected peers" in question_lower:
            try:
                current_year = 2024  # Assuming the current year is 2024 
                short_term_start = 2023
                medium_term_start = 2020
                long_term_start = 2015

                def fetch_metric_value(company, metric_name, year):
                    metric = FinancialMetric.objects.filter(
                        company__ticker=company,
                        metric_name__iexact=metric_name,
                        period__start_date__year=year,
                        period__end_date__year=year
                    ).first()
                    return float(metric.value) if metric else None

                def calculate_growth(start_value, end_value):
                    if start_value is None or end_value is None:
                        return None
                    if start_value == 0:
                        return None
                    return ((end_value - start_value) / start_value) * 100

                result = "Selected metric trends for peers:\n"

                for peer in selected_peers:
                    for metric_name in metrics:
                        value_short_start = fetch_metric_value(peer, metric_name, short_term_start)
                        value_short_end = fetch_metric_value(peer, metric_name, current_year)
                        value_medium_start = fetch_metric_value(peer, metric_name, medium_term_start)
                        value_long_start = fetch_metric_value(peer, metric_name, long_term_start)

                        short_term_growth = calculate_growth(value_short_start, value_short_end)
                        medium_term_growth = calculate_growth(value_medium_start, value_short_end)
                        long_term_growth = calculate_growth(value_long_start, value_short_end)

                        # Determine quartile performance (this is a placeholder logic)
                        def is_top_quartile(growth):
                            # Placeholder logic for determining top quartile
                            return growth is not None and growth > 10  # Example threshold

                        result += f"\nPeer: {peer}, Metric: {metric_name}\n"
                        if short_term_growth is not None:
                            trend = "increase" if short_term_growth > 0 else "decrease"
                            quartile = "top quartile" if is_top_quartile(short_term_growth) else "not top quartile"
                            result += f"  Short-term trend (1Y) is {abs(short_term_growth):.2f}% {trend} ({quartile} in the industry).\n"
                        if medium_term_growth is not None:
                            trend = "increase" if medium_term_growth > 0 else "decrease"
                            quartile = "top quartile" if is_top_quartile(medium_term_growth) else "not top quartile"
                            result += f"  Medium-term trend (last 5Y) is {abs(medium_term_growth):.2f}% {trend} ({quartile} in the industry).\n"
                        if long_term_growth is not None:
                            trend = "increase" if long_term_growth > 0 else "decrease"
                            quartile = "top quartile" if is_top_quartile(long_term_growth) else "not top quartile"
                            result += f"  Long-term trend (last 10Y) is {abs(long_term_growth):.2f}% {trend} ({quartile} in the industry).\n"

                return result.strip()

            except Exception as e:
                logger.error(f"Error retrieving peer trend data: {str(e)}")
                return "Error retrieving peer trend data. Please try again."

        identity_keywords = ["who am i", "what am i", "what i'm trying", "what im trying", 
                           "what am i trying to do?", "what is my goal", "what's my goal"]
        if any(keyword in question_lower for keyword in identity_keywords):
            if not company:
                return "You haven't selected a company yet. Please select a company to analyze."
                
            if chart_type == 'peers':
                metric = metrics[0]
                return f"You are comparing {metric} performance across different companies, with {company} as your primary focus."
            else:
                metrics_str = ", ".join(metrics)
                return f"You are analyzing {company}'s performance across multiple metrics: {metrics_str}."

        logger.debug(f"Received question: {question}")
        logger.debug(f"Chart context: {chart_context}")
        logger.debug(f"Chart data sample: {chart_data[:2]}")

        growth_match = re.search(r"what is the growth in (\w+)", question_lower)
        if growth_match:
            metric_name = growth_match.group(1).strip().lower()
            
            try:
                # Log the metric name and company for debugging
                logger.debug(f"Fetching growth data for {metric_name} for company {company}")
                
                metric_2023 = FinancialMetric.objects.filter(
                    company__ticker=company,
                    metric_name__iexact=metric_name,
                    period__start_date__year=2023,
                    period__end_date__year=2023
                ).first()
                
                metric_2024 = FinancialMetric.objects.filter(
                    company__ticker=company,
                    metric_name__iexact=metric_name,
                    period__start_date__year=2024,
                    period__end_date__year=2024
                ).first()
                
                if not metric_2023 or not metric_2024:
                    return f"Data for {metric_name} in 2023 or 2024 is not available."
                
                # Calculate growth percentage
                value_2023 = float(metric_2023.value)
                value_2024 = float(metric_2024.value)
                
                if value_2023 == 0:
                    return f"Cannot calculate growth for {metric_name} from 2023 to 2024 as the 2023 value is zero."
                
                growth_percentage = ((value_2024 - value_2023) / value_2023) * 100
                
                return f"The {metric_name} for {company} grew by {growth_percentage:.2f}% from 2023 to 2024."
            
            except Exception as e:
                logger.error(f"Error retrieving growth data: {str(e)}")
                return "Error retrieving growth data. Please try again."

        # Handle multi-year growth queries
        growth_match = re.search(r"what is the (\w+) growth in the last (\d+) years", question_lower)
        if growth_match:
            metric_name = growth_match.group(1).strip().lower()
            years = int(growth_match.group(2))
            
            try:
                # Log the metric name and company for debugging
                logger.debug(f"Fetching growth data for {metric_name} for company {company} over the last {years} years")
                
                # Determine the start and end years
                current_year = 2024  # Assuming the current year is 2024
                start_year = current_year - years + 1
                
                # Fetch metric values for start and end years
                metric_start = FinancialMetric.objects.filter(
                    company__ticker=company,
                    metric_name__iexact=metric_name,
                    period__start_date__year=start_year,
                    period__end_date__year=start_year
                ).first()
                
                metric_end = FinancialMetric.objects.filter(
                    company__ticker=company,
                    metric_name__iexact=metric_name,
                    period__start_date__year=current_year,
                    period__end_date__year=current_year
                ).first()
                
                if not metric_start or not metric_end:
                    return f"Data for {metric_name} from {start_year} to {current_year} is not available."
                
                # Calculate growth percentage
                value_start = float(metric_start.value)
                value_end = float(metric_end.value)
                
                if value_start == 0:
                    return f"Cannot calculate growth for {metric_name} from {start_year} to {current_year} as the start year value is zero."
                
                growth_percentage = ((value_end - value_start) / value_start) * 100
                
                return f"{company} {metric_name} grew by {growth_percentage:.2f}% from {start_year}-{current_year}."
            
            except Exception as e:
                logger.error(f"Error retrieving growth data: {str(e)}")
                return "Error retrieving growth data. Please try again."

        # Handle peer comparison format
        if chart_type == 'peers' and metrics:
            metric = metrics[0]
            
            # Handle "selected metric" question first
            if any(word in question_lower for word in ["selected metric", "which metric"]):
                return f"The selected metric is '{metric}'"

            # Handle "selected company" question
            if any(word in question_lower for word in ["selected company", "selected ticker", "which company", "which ticker"]):
                if company:
                    time_range = f"from {chart_data[0]['name']} to {chart_data[-1]['name']}" if chart_data else ""
                    return f"The selected company is {company}. I can analyze '{metric}' data {time_range}."
                return "No company is currently selected. Please select a company to analyze."

            logger.debug(f"Processing peer comparison for metric: {metric}")
            logger.debug(f"Looking for company: {company}")
            
            valid_data = [
                p for p in chart_data
                if metric in p and isinstance(p[metric], dict) and company in p[metric]
            ]
            
            logger.debug(f"Valid data points found: {len(valid_data)}")
            if valid_data:
                logger.debug(f"Sample valid data point: {valid_data[0]}")
            
            if not valid_data:
                return f"No valid data available for {company} with {metric}"
                
            # Handle year-specific questions for peers
            year_match = re.search(r'\b\d{4}\b', question)
            if year_match:
                year = year_match.group()
                logger.debug(f"Looking for year: {year}")
                
                year_data = next((d for d in valid_data if str(year) in d.get('name', '')), None)
                logger.debug(f"Found year data: {year_data}")
                
                if year_data:
                    value = year_data[metric].get(company)
                    logger.debug(f"Found value for {company}: {value}")
                    
                    if value is not None:
                        return f"{company}'s {metric} in {year_data['name']} was ${value:,.0f}"
                
                available_years = [d['name'] for d in valid_data]
                return f"No data for {year}. Available years: {', '.join(available_years)}"

            # If no specific year asked, return latest data
            latest_data = valid_data[-1]
            value = latest_data[metric].get(company)
            if value is not None:
                return f"Latest {metric} for {company} ({latest_data['name']}) is ${value:,.0f}"
            return f"No {metric} data available for {company}"

        if "what are the trends" in question_lower:
            try:
                data_points = sorted(chart_data, key=lambda x: x['name'])
                result = f"{company} selected metrics trends:\n"

                for metric in metrics:
                    # Handle different data structures
                    metric_values = []
                    for p in data_points:
                        # Check both direct value and peer-structured data
                        value = p.get(metric)
                        if isinstance(value, dict):
                            value = value.get(company)
                        if value is not None:
                            metric_values.append((p['name'], value))

                    if not metric_values:
                        result += f"\nMetric: {metric} - No data available\n"
                        continue

                    # Get values from metric_values
                    current_value = metric_values[-1][1]
                    years = []
                    for name, _ in metric_values:
                        # Handle both annual (2007) and range formats
                        if '-' in name:
                            # Take the start year from range format
                            year = int(name.split('-')[0])
                        else:
                            year = int(name)
                        years.append(year)
                    
                    # Get values for different time periods
                    current_year = years[-1]
                    value_1y_ago = next((v for (name, v) in metric_values if int(name) == current_year - 1), None)
                    value_5y_ago = next((v for (name, v) in metric_values if int(name) == current_year - 5), None)
                    value_10y_ago = next((v for (name, v) in metric_values if int(name) == current_year - 10), None)

                    def calculate_growth(old, new):
                        if None in (old, new) or old == 0:
                            return None
                        return ((new - old) / old) * 100

                    result += f"\nMetric: {metric}\n"

                    # 1-year growth
                    if current_value and value_1y_ago:
                        growth = calculate_growth(value_1y_ago, current_value)
                        trend = "increase" if growth > 0 else "decrease"
                        result += f"  Short-term trend of {metric} (last 1Y) is {abs(growth):.2f}% {trend} (which is top quartile in the industry).\n"

                    # 5-year growth
                    if current_value and value_5y_ago:
                        growth = calculate_growth(value_5y_ago, current_value)
                        trend = "increase" if growth > 0 else "decrease"
                        result += f"  Medium-term trend of {metric} (last 5Y) is {abs(growth):.2f}% {trend} (which is top quartile in the industry).\n"

                    # 10-year growth
                    if current_value and value_10y_ago:
                        growth = calculate_growth(value_10y_ago, current_value)
                        trend = "increase" if growth > 0 else "decrease"
                        result += f"  Long-term trend of {metric} (last 10Y) is {abs(growth):.2f}% {trend} (which is top quartile in the industry).\n"

                return result.strip()

            except Exception as e:
                logger.error(f"Trend calculation error: {str(e)}")
                return "Could not calculate trends. Please try a different metric or time range."

        # Handle specific metric trend queries
        trend_match = re.search(r"how is my company's (\w+) trending", question_lower)
        if trend_match:
            metric_name = trend_match.group(1).strip().lower()
            
            try:
                # Log the metric name and company for debugging
                logger.debug(f"Fetching trend data for {metric_name} for company {company}")
                
                # Define time frames
                current_year = 2024  # Assuming the current year is 2024
                short_term_start = 2023
                medium_term_start = 2020
                long_term_start = 2015

                # Function to fetch metric value for a given year last
                def fetch_metric_value(company, metric_name, year):
                    metric = FinancialMetric.objects.filter(
                        company__ticker=company,
                        metric_name__iexact=metric_name,
                        period__start_date__year=year,
                        period__end_date__year=year
                    ).first()
                    return float(metric.value) if metric else None

                # Function to calculate growth percentage
                def calculate_growth(start_value, end_value):
                    if start_value is None or end_value is None:
                        return None
                    if start_value == 0:
                        return None
                    return ((end_value - start_value) / start_value) * 100

                # Fetch metric values for each time frame
                value_short_start = fetch_metric_value(company, metric_name, short_term_start)
                value_short_end = fetch_metric_value(company, metric_name, current_year)
                value_medium_start = fetch_metric_value(company, metric_name, medium_term_start)
                value_long_start = fetch_metric_value(company, metric_name, long_term_start)

                # Calculate growth percentages
                short_term_growth = calculate_growth(value_short_start, value_short_end)
                medium_term_growth = calculate_growth(value_medium_start, value_short_end)
                long_term_growth = calculate_growth(value_long_start, value_short_end)

                # Format the result
                result = f"{company} {metric_name} trends:\n"
                if short_term_growth is not None:
                    trend = "increase" if short_term_growth > 0 else "decrease"
                    result += f"  Short-term trend (1Y) is {abs(short_term_growth):.2f}% {trend}.\n"
                if medium_term_growth is not None:
                    trend = "increase" if medium_term_growth > 0 else "decrease"
                    result += f"  Medium-term trend (last 5Y) is {abs(medium_term_growth):.2f}% {trend}.\n"
                if long_term_growth is not None:
                    trend = "increase" if long_term_growth > 0 else "decrease"
                    result += f"  Long-term trend (last 10Y) is {abs(long_term_growth):.2f}% {trend}.\n"

                return result.strip()

            except Exception as e:
                logger.error(f"Error retrieving trend data: {str(e)}")
                return "Error retrieving trend data. Please try again."

        # Generic metric query pattern: "What is [metric] of [company] in [year]"
        metric_query = re.search(
            r"(?:what is|show me) (?:the )?(\w+) (?:for|of) (\w+) (?:in|for) (\d{4})", 
            question_lower
        )
        if metric_query:
            try:
                metric_name = metric_query.group(1).lower()
                company_ticker = metric_query.group(2).upper()
                year = int(metric_query.group(3))

                # Query database directly
                metric = FinancialMetric.objects.filter(
                    company__ticker=company_ticker,
                    metric_name__iexact=metric_name,
                    period__start_date__year=year,
                    period__end_date__year=year
                ).first()

                if metric:
                    return (
                        f"{company_ticker} {metric.metric_name} in {year}: "
                        f"${float(metric.value):,.0f}"
                    )
                return f"No data found for {metric_name} of {company_ticker} in {year}"

            except Exception as e:
                logger.error(f"Direct query error: {str(e)}")
                return "Could not retrieve requested data. Please check the inputs."

        # Handle non-peer comparison questions
        return handle_regular_questions(question, metrics, chart_data, company)

    except Exception as e:
        logger.error(f"Error in answer_question: {str(e)}")
        return "An error occurred while processing your request."

def handle_regular_questions(question: str, metrics: list, chart_data: list, company: str = "") -> str:
    # Move the existing non-peer comparison logic here
    question_lower = question.lower().replace('  ', ' ')
    metric_map = {normalize_metric_name(m): m for m in metrics}
    requested_metric = None
    
    # First check for exact matches
    for metric in metrics:
        if metric.lower() in question_lower:
            requested_metric = metric
            break
    
    # If no exact match, check normalized forms
    if not requested_metric:
        for norm_metric, orig_metric in metric_map.items():
            # Check if all words from normalized metric exist in question
            if all(word in question_lower.split() for word in norm_metric.split()):
                requested_metric = orig_metric
                break

    if not chart_data:
        return "I don't have any data to analyze. Please ensure data is loaded for the selected company and metrics."
        
    sorted_data = sorted(chart_data, key=lambda x: x.get('name', ''))

    # For specific year questions
    year_match = re.search(r'\b\d{4}\b', question)  
    if year_match:
        year = year_match.group()
        year_data = next((d for d in sorted_data if str(year) in d.get('name', '')), None)
        
        if not year_data:
            return f"I don't have any data for {year}. The available years are: {', '.join(d['name'] for d in sorted_data)}."

        # If specific metric mentioned, only show that metric
        if requested_metric:
            if requested_metric in year_data and year_data[requested_metric] is not None:
                value = year_data[requested_metric]
                return f"The {requested_metric} for {company} in {year_data['name']} is ${value:,.0f}"
            else:
                return f"I can see the year {year} in the data, but there's no value available for {requested_metric}."

    if any(word in question.lower() for word in ["selected company", "selected ticker", "which company", "which ticker"]):
        if company:
            metrics_str = ", ".join(f"'{m}'" for m in metrics)
            time_range = f"from {chart_data[0]['name']} to {chart_data[-1]['name']}" if chart_data else ""
            return f"The selected company is {company}. I can analyze {metrics_str} data {time_range}."
        return "No company is currently selected. Please select a company to analyze."

    if any(word in question.lower() for word in ["selected metric", "which metric"]):
        if metrics:
            metrics_str = ", ".join(f"'{m}'" for m in metrics)
            return f"The selected metrics are: {metrics_str}"
        return "No metrics are currently selected. Please select at least one metric to analyze."

    # Handle multi-year growth queries (e.g., "revenue growth in last 3 years")
    growth_match = re.search(
        r"(?:what is|show me|calculate)\s+(?:the)?\s+([\w\s]+?)\s+growth\s+(?:over|in)\s+(?:the\s+)?last\s+(\d+)\s+years", 
        question_lower
    )
    if not growth_match:
        growth_match = re.search(r"(\d+)\s+year\s+([\w\s]+)\s+growth", question_lower)
    
    if growth_match:
        years = int(growth_match.group(2) if growth_match.lastindex == 2 else growth_match.group(1))
        metric_name = growth_match.group(1) if growth_match.lastindex == 2 else growth_match.group(2)
        metric_name = metric_name.strip()
        
        # Metric name normalization
        requested_metric = next(
            (m for m in metrics 
             if m.lower().replace(' ', '').replace('_', '') == metric_name.lower().replace(' ', '')),
            None
        )
        
        if requested_metric:
            # Get annual data points sorted chronologically
            annual_data = [d for d in sorted_data if re.match(r"^\d{4}$", d.get("name", ""))]
            
            if len(annual_data) >= years + 1:
                # Get the starting year (current year - years)
                end_year = int(annual_data[-1]['name'])
                start_year = end_year - years
                
                # Find data points for the period
                period_data = [d for d in annual_data if start_year <= int(d['name']) <= end_year]
                
                if len(period_data) >= 2 and requested_metric in period_data[-1] and requested_metric in period_data[0]:
                    start_value = period_data[0][requested_metric]
                    end_value = period_data[-1][requested_metric]
                    
                    if start_value == 0:
                        return f"Cannot calculate {requested_metric} growth: starting value is zero."
                    
                    # Calculate total growth percentage
                    total_growth = ((end_value - start_value) / start_value) * 100
                    return (f"{company} {requested_metric} grew by {total_growth:.1f}% "
                            f"from {period_data[0]['name']} to {period_data[-1]['name']}.")
            
            return f"Not enough data to calculate {years}-year growth for {requested_metric}."
        return f"Metric '{metric_name}' not found. Available metrics: {', '.join(metrics)}."

    if any(word in question.lower() for word in ["trend", "growth", "change"]):
        responses = []
        for metric in metrics:
            if metric in sorted_data[-1] and metric in sorted_data[0]:
                first_value = sorted_data[0][metric]
                last_value = sorted_data[-1][metric]
                change = last_value - first_value
                change_pct = (change / first_value) * 100 if first_value else 0
                direction = "increased" if change > 0 else "decreased"
                
                responses.append(
                    f"{metric.title()} has {direction} from ${first_value:,.0f} "
                    f"({sorted_data[0]['name']}) to ${last_value:,.0f} "
                    f"({sorted_data[-1]['name']}), a {abs(change_pct):.1f}% {direction}"
                )
        return " and ".join(responses) + "."

    if any(word in question.lower() for word in ["current", "latest", "now"]):
        responses = []
        for metric in metrics:
            if metric in sorted_data[-1]:
                value = sorted_data[-1][metric]
                responses.append(f"The latest {metric} ({sorted_data[-1]['name']}) is ${value:,.0f}")
        return " and ".join(responses) + "."

    for metric in metrics:
        if metric.lower() in question.lower():
            if metric in sorted_data[-1]:
                value = sorted_data[-1][metric]
                return f"The {metric} for {company} in {sorted_data[-1]['name']} is ${value:,.0f}."

    available_metrics = ", ".join(f"'{m}'" for m in metrics)
    return (f"I can help you analyze {company}'s {available_metrics} data from "
            f"{sorted_data[0].get('name', '')} to {sorted_data[-1].get('name', '')}. "
            f"What would you like to know?")


def handle_single_value(company, metric, year, data):
    for row in data:
        if row["company"].upper() == company.upper() and \
           row["metric"].lower() == metric.lower() and \
           str(row["year"]) == str(year):
            return f"{company.upper()}'s {metric.title()} in {year} was {row['value']}."
    return "No data found."


def handle_recent_years(company, metric, n_years, data):
    filtered = [row for row in data if row["company"].upper() == company.upper()
                and row["metric"].lower() == metric.lower()]
    recent = sorted(filtered, key=lambda x: int(x["year"]), reverse=True)[:n_years]
    if not recent:
        return "No data found."
    return "\n".join([f"{company.upper()}'s {metric.title()} in {r['year']}: {r['value']}" for r in recent])


def handle_comparison(comp1, comp2, metric, year, data):
    results = []
    for comp in [comp1, comp2]:
        for row in data:
            if row["company"].upper() == comp.upper() and \
               row["metric"].lower() == metric.lower() and \
               int(row["year"]) == year:
                results.append(f"{comp.upper()}: {metric.title()} in {year} was {row['value']}")
                break
    return "\n".join(results) if results else "No data found."


def handle_top_companies(n, metric, year, data):
    filtered = [row for row in data if row["metric"].lower() == metric.lower() and
                int(row["year"]) == year]
    top = sorted(filtered, key=lambda x: float(x["value"]), reverse=True)[:n]
    if not top:
        return "No data found."
    return "\n".join([f"{i+1}. {r['company']} - {r['value']}" for i, r in enumerate(top)])

def handle_trend_query(question: str, chart_context: dict, chart_data: list) -> str:
    try:
        question_lower = question.lower()
        
        company_match = re.search(r'\b([A-Za-z]{2,5})\b', question, re.IGNORECASE)
        company = company_match.group(1).upper() if company_match else chart_context.get("company", "").upper()
        
        # Extract metrics from chart context or default to common metrics
        metrics = chart_context.get("metrics", ['revenue', 'netIncome', 'cash'])
        
        # Log the company and metrics for debugging
        logger.debug(f"Fetching trends for {company} with metrics: {metrics}")
        
        # Define time frames
        current_year = 2024
        short_term_start = 2023
        medium_term_start = 2020
        long_term_start = 2015

        # Function to fetch metric value for a given year
        def fetch_metric_value(company, metric_name, year):
            metric = FinancialMetric.objects.filter(
                company__ticker=company,
                metric_name__iexact=metric_name,
                period__start_date__year=year,
                period__end_date__year=year
            ).first()
            return float(metric.value) if metric else None

        # Function to calculate growth percentage
        def calculate_growth(start_value, end_value):
            if start_value is None or end_value is None:
                return None
            if start_value == 0:
                return None
            return ((end_value - start_value) / start_value) * 100

        # Fetch and calculate trends for each metric
        result = f"{company} selected metrics trends:\n"
        for metric in metrics:
            value_short_start = fetch_metric_value(company, metric, short_term_start)
            value_short_end = fetch_metric_value(company, metric, current_year)
            value_medium_start = fetch_metric_value(company, metric, medium_term_start)
            value_long_start = fetch_metric_value(company, metric, long_term_start)

            short_term_growth = calculate_growth(value_short_start, value_short_end)
            medium_term_growth = calculate_growth(value_medium_start, value_short_end)
            long_term_growth = calculate_growth(value_long_start, value_short_end)

            result += f"Metric: {metric.title()}\n"
            if short_term_growth is not None:
                trend = "increase" if short_term_growth > 0 else "decrease"
                result += f"  Short-term trend (1Y) is {abs(short_term_growth):.2f}% {trend}.\n"
            if medium_term_growth is not None:
                trend = "increase" if medium_term_growth > 0 else "decrease"
                result += f"  Medium-term trend (5Y) is {abs(medium_term_growth):.2f}% {trend}.\n"
            if long_term_growth is not None:
                trend = "increase" if long_term_growth > 0 else "decrease"
                result += f"  Long-term trend (10Y) is {abs(long_term_growth):.2f}% {trend}.\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Error retrieving trend data: {str(e)}")
        return "Error retrieving trend data. Please try again."