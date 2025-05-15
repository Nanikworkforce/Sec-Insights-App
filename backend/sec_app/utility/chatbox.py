import re
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def normalize_metric_name(metric: str) -> str:
    """Convert camelCase to space-separated lowercase"""
    normalized = re.sub(r'(?<!^)(?=[A-Z])', ' ', metric).lower()
    return normalized

def answer_question(question: str, chart_context: dict, chart_data: list) -> str:
    try:
        company = chart_context.get("company", "")
        metrics = chart_context.get("metrics", [])

        # Normalize the question to handle different formats
        question_lower = question.lower().replace('  ', ' ')
        
        # Create a mapping of normalized metric names to original metrics
        metric_map = {normalize_metric_name(m): m for m in metrics}
        
        # Determine the requested metric
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

    except Exception as e:
        logger.error(f"Error in answer_question: {str(e)}")
        return "I apologize, but I encountered an error analyzing the data. Please try asking in a different way."


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
