import re
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def answer_question(question: str, chart_context: dict, chart_data: list) -> str:
    try:
        company = chart_context.get("company", "")
        period = chart_context.get("period", "")
        metrics = chart_context.get("metrics", [])
        
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

        if not chart_data:
            return f"No data available for {company}."
        sorted_data = sorted(chart_data, key=lambda x: x.get('name', ''))
        
        if "growth" in question.lower() and "percentage" in question.lower():
            years = re.findall(r'\b\d{4}\b', question)
            if len(years) == 2:
                start_year, end_year = years
                start_data = next((d for d in sorted_data if str(start_year) in d.get('name', '')), None)
                end_data = next((d for d in sorted_data if str(end_year) in d.get('name', '')), None)
                
                if start_data and end_data:
                    responses = []
                    for metric in metrics:
                        if metric in start_data and metric in end_data:
                            start_value = start_data[metric]
                            end_value = end_data[metric]
                            if start_value and start_value != 0:  # Avoid division by zero
                                change = end_value - start_value
                                change_pct = (change / start_value) * 100
                                direction = "increased" if change > 0 else "decreased"
                                responses.append(
                                    f"{metric} has {direction} by {abs(change_pct):.1f}% "
                                    f"from ${start_value:,.0f} ({start_year}) "
                                    f"to ${end_value:,.0f} ({end_year})"
                                )
                    return " and ".join(responses) + "." if responses else f"No valid data found for comparison between {start_year} and {end_year}."
                return f"Unable to find data for both {start_year} and {end_year}."

        year_match = re.search(r'\b\d{4}\b', question)  
        if year_match:
            year = year_match.group()
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
