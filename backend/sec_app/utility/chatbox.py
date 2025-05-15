import re
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def answer_question(question: str, chart_context: dict, chart_data: list) -> str:
    try:
        company = chart_context.get("company", "")
        period = chart_context.get("period", "")
        metrics = chart_context.get("metrics", [])
        
        if not chart_data:
            return f"No data available for {company}."

        # Sort data chronologically
        sorted_data = sorted(chart_data, key=lambda x: x.get('name', ''))
        
        # Get latest and earliest data points
        latest_data = sorted_data[-1] if sorted_data else {}
        earliest_data = sorted_data[0] if sorted_data else {}
        
        # For specific value questions (e.g., "what is the revenue in 2024?")
        year_match = re.search(r'\b\d{4}\b', question)  # Find 4-digit year in question
        if year_match:
            year = year_match.group()
            # Find data point for that year
            year_data = next((d for d in sorted_data if str(year) in d.get('name', '')), None)
            
            if year_data:
                responses = []
                for metric in metrics:
                    if metric in year_data:
                        value = year_data[metric]
                        responses.append(f"The {metric} for {company} in {year_data['name']} is ${value:,.0f}")
                return " and ".join(responses) + "."
            else:
                return f"No data available for {company} in {year}."

        # For trend/growth questions
        if any(word in question.lower() for word in ["trend", "growth", "change"]):
            responses = []
            for metric in metrics:
                if metric in latest_data and metric in earliest_data:
                    first_value = earliest_data[metric]
                    last_value = latest_data[metric]
                    change = last_value - first_value
                    change_pct = (change / first_value) * 100 if first_value else 0
                    direction = "increased" if change > 0 else "decreased"
                    
                    responses.append(
                        f"{metric.title()} has {direction} from ${first_value:,.0f} "
                        f"({earliest_data['name']}) to ${last_value:,.0f} "
                        f"({latest_data['name']}), a {abs(change_pct):.1f}% {direction}"
                    )
            return " and ".join(responses) + "."

        # For latest value questions
        if any(word in question.lower() for word in ["current", "latest", "now"]):
            responses = []
            for metric in metrics:
                if metric in latest_data:
                    value = latest_data[metric]
                    responses.append(f"The latest {metric} ({latest_data['name']}) is ${value:,.0f}")
            return " and ".join(responses) + "."

        # For specific metric questions (e.g., "what is the revenue?")
        for metric in metrics:
            if metric.lower() in question.lower():
                if metric in latest_data:
                    value = latest_data[metric]
                    return f"The {metric} for {company} in {latest_data['name']} is ${value:,.0f}."

        # Default response
        available_metrics = ", ".join(f"'{m}'" for m in metrics)
        return (f"I can help you analyze {company}'s {available_metrics} data from "
                f"{earliest_data.get('name', '')} to {latest_data.get('name', '')}. "
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
