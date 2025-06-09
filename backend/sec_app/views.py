from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets,filters
from rest_framework.views import APIView
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models.company import Company
from .models.analysis import SentimentAnalysis
from .models.period import FinancialPeriod
from .models.filling import FilingDocument
from .models.metric import FinancialMetric
from .models.chatlog import ChatLog
from django.db.models import Avg, Sum
from .models.query import Query
from .serializer import *
from rest_framework.decorators import api_view
from .api_client import fetch_financial_data
from .utility.utils import *
from django.http import JsonResponse
import logging
import requests
from django.conf import settings 
import pandas as pd
import os 
from .utility.chatbox import answer_question
logger = logging.getLogger(__name__)
from .utility.bot import *
from django.db import transaction
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from .utility.bot import fetch_google_news

@csrf_exempt
@api_view(["GET"])
def load_data(request):
    if request.GET.get("secret") != "letmein":
        return Response({"error": "Unauthorized"}, status=401)

    try:
        fixture_path = os.path.join(settings.BASE_DIR, "sec_app", "fixtures", "all_data.json")
        call_command("loaddata", fixture_path, verbosity=1)
        return Response({"status": "success"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

class ChatbotAPIView(APIView):
    def post(self, request):
        try:
            question = request.data.get("question")
            payload = request.data.get("payload", {})
            context = {}

            # Check for introspective questions first
            if is_introspective_question(question):
                return Response({"answer": describe_payload_intent(payload)})

            keywords = extract_keywords(question)

            logger.info(f"Payload received: {payload}")
            logger.info(f"Keywords extracted: {keywords}")

            # Handle invalid company/ticker
            if keywords.get("invalid_company"):
                return Response({
                    "answer": f"'{keywords['invalid_company']}' is not a valid ticker or company. Please provide a valid ticker or company name."
                })

            # Handle news queries
            if keywords.get("news_company"):
                news_company = keywords["news_company"]
                # Use the fetch_google_news function from bot.py to get the news link
                try:
                    news_link = fetch_google_news(news_company)
                    answer = f"Here are the latest news headlines for {news_company}: {news_link}"
                except Exception as e:
                    logger.error(f"Error fetching news link: {str(e)}")
                    answer = f"Here are the latest news headlines for {news_company}: (News link unavailable. This is a placeholder. News integration coming soon.)"
                with transaction.atomic():
                    ChatLog.objects.create(
                        question=question,
                        answer=answer,
                    )
                return Response({"answer": answer})

            # Step 1: If we have company and metric in keywords, use those directly
            if keywords.get("company") and keywords.get("metric"):
                context = {
                    "company": keywords["company"],
                    "metric_name": to_camel_case(keywords["metric"]),
                    "year": keywords.get("year"),
                    "time_range": keywords.get("time_range"),
                    "year_range": keywords.get("year_range"),
                    "growth": keywords.get("growth", False)
                }
                answer = query_data_from_db(context)
            # Step 1.5: If only company or only metric is present, ask for clarification
            elif keywords.get("company") and not keywords.get("metric"):
                answer = f"What would you like to know about {keywords['company']}? Please refine your search with a metric or year."
            elif keywords.get("metric") and not keywords.get("company"):
                answer = f"Which company would you like to know about {keywords['metric']}? Please specify a company."
            # Step 2: Valid keywords with growth intent
            elif keywords.get("growth"):
                # Use payload company if not in keywords
                company = keywords.get("company") or payload.get("company")
                metric = keywords.get("metric") or (payload["metric_name"][0] if isinstance(payload.get("metric_name"), list) else payload.get("metric_name"))
                context = {
                    "company": company,
                    "metric_name": to_camel_case(metric) if metric else None,
                    "growth": True
                }
                answer = query_data_from_db(context)
            # Step 3: Valid company in keywords
            elif keywords.get("company"):
                context = keywords
                if "metric" in context:
                    context["metric_name"] = context["metric"]
                answer = query_data_from_db(context)
            # Step 4: If not all keywords, check payload
            elif payload and payload.get("company"):
                # Check if multiple companies are selected
                companies = payload.get("companies", [])
                if len(companies) > 1 and not keywords.get("company"):
                    # If multiple companies and user didn't specify one, ask them to choose
                    company_list = ", ".join(companies)
                    answer = f"There are {len(companies)} companies selected on the chart, {company_list}. Please specify which company you want to find its {payload['metric_name'][0] if isinstance(payload['metric_name'], list) else payload['metric_name']}."
                    return Response({"answer": answer})

                # Get the metric the user is asking about
                asked_metric = keywords.get("metric", "").lower() if keywords.get("metric") else None

                # If user asked for a specific metric, find it in payload metrics
                if asked_metric:
                    metric_to_use = to_camel_case(asked_metric)  # Always use camelCase for metric name
                else:
                    # Default to first metric if no specific metric asked
                    metric_to_use = payload["metric_name"][0] if isinstance(payload["metric_name"], list) else payload["metric_name"]

                # Use payload data
                context = {
                    "company": payload["company"],
                    "metric_name": metric_to_use,
                    "year": keywords.get("year") or payload.get("year"),
                }
                # Add time_range and year_range if present in keywords
                if keywords.get("time_range"):
                    context["time_range"] = keywords["time_range"]
                if keywords.get("year_range"):
                    context["year_range"] = keywords["year_range"]
                logger.info(f"Using payload context: {context}")
                answer = query_data_from_db(context)
            # Step 5: If neither, fallback
            else:
                answer = "Can you please specify the company, metric, or year you're interested in?"
                context = {}

            # Save to chat log
            with transaction.atomic():
                ChatLog.objects.create(
                    question=question,
                    answer=answer,
                )

            return Response({"answer": answer})
        except Exception as e:
            logger.error(f"Error in ChatbotAPIView: {str(e)}")
            return Response({
                "error": "Failed to process question. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_sec_data(request):
    return Response({"message": "Hello, world!"})

@api_view(['GET'])
def extract_financials(request):
    ticker = request.GET.get('ticker', 'AAPL')
    
    data = fetch_financial_data(ticker)
    if data and data.get('filings'):
        try:
            # Log sample filing details
            sample_filing = data['filings'][0]
            # Check if the data has the expected structure for save_financial_data_to_db
            # Check if there's any 'data' field in the filing that would contain metrics
            if 'data' in sample_filing:
                logger.info(f"Sample metrics: {list(sample_filing['data'].keys())[:5]}")
            else:
                logger.warning("No 'data' field found in filing - metrics may not be saved")
            
            save_financial_data_to_db(data)
            return JsonResponse({
                "message": f"Data fetched and saved for {ticker}",
                "filings_count": len(data['filings']),
                "sample_filing": {
                    "type": sample_filing.get('formType'),
                    "date": sample_filing.get('filedAt'),
                    "docs": sample_filing.get('documentFormatFiles')
                } 
            })
        except Exception as e:
            return JsonResponse({"error": f"Error saving data: {str(e)}"}, status=500)
    return JsonResponse({"error": "No valid 10-K filings found"}, status=500)

@api_view(['GET'])
def test_sec_api(request):
    ticker = request.GET.get('ticker', 'AAPL')
    try:
        api_key = settings.SEC_API_KEY
        headers = {'Authorization': api_key}
        
        # Test direct API call
        api_url = "https://api.sec-api.io/api/search"
        payload = {
            "query": {
                "query_string": {
                    "query": f"ticker:{ticker} AND formType:\"10-K\""
                }
            },
            "from": "0",
            "size": "10",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        return JsonResponse({
            'status_code': response.status_code,
            'content': response.text[:1000] if response.text else None,
            'headers': dict(response.headers)
        })
        
    except Exception as e:
        logger.error(f"Error testing API: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['ticker', 'cik']
    search_fields = ['ticker', 'name', 'cik']
    

class FilingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FilingDocument.objects.all()
    serializer_class = FilingDocumentSerializer

class FinancialMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FinancialMetric.objects.all()
    serializer_class = FinancialMetricSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['company__ticker', 'company__name', 'metric_name', 'period__id']
    search_fields = ['company__name', 'company__ticker', 'metric_name']
    
    def get_queryset(self):
        queryset = FinancialMetric.objects.all()
        count = queryset.count()
        logger.info(f"FinancialMetricViewSet: Found {count} metrics in database")
        if count == 0:
            company_count = Company.objects.count()
            period_count = FinancialPeriod.objects.count()
            logger.info(f"Diagnostic: Found {company_count} companies and {period_count} periods")
        return queryset

class ChartDataAPIView(APIView):
    def get(self, request):
        try:
            tickers = request.GET.get("tickers", "").split(',')
            metric = request.GET.get("metric", "revenue")
            
            if not tickers or not tickers[0]:  # Check if tickers list is empty or contains empty string
                return Response(
                    {"error": "Tickers are required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            all_metrics = []
            all_periods = set()
            
            for ticker in tickers:
                company = Company.objects.filter(ticker=ticker).first()
                if company:
                    
                    metrics = FinancialMetric.objects.filter(
                        company=company,
                        metric_name=metric
                    ).select_related('period')
                    
                    # Log the number of metrics found
                    logger.info(f"Found {metrics.count()} metrics for {ticker}")
                    
                    for m in metrics:
                        period = m.period.period
                        all_periods.add(period)
                        all_metrics.append({
                            "ticker": ticker,
                            "period": period,
                            "value": float(m.value) if m.value is not None else 0
                        })
            
            # Organize data by period
            period_data = []
            for period in sorted(all_periods):
                period_values = {
                    "period": period,
                    "values": {
                        metric["ticker"]: metric["value"]
                        for metric in all_metrics
                        if metric["period"] == period
                    }
                }
                period_data.append(period_values)
            
            # Log the response data
            return Response({
                "tickers": tickers,
                "metrics": period_data,
                "selected_metric": metric
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def get_available_metrics(request):
        metrics = FinancialMetric.objects.values_list('metric_name', flat=True).distinct()
        return Response({
            "metrics": list(metrics)
        })

class InsightsAPIView(APIView):
    def get(self, request):
        ticker = request.GET.get("ticker")
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        company = Company.objects.filter(ticker=ticker).first()
        if not company:
            return Response({"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        
        insights = []
        revenue_trend = FinancialMetric.objects.filter(period__company=company, name="Revenue").order_by("period__year")
        
        if revenue_trend.count() >= 5:
            last_5_years = [rev.value for rev in revenue_trend][-5:]
            if last_5_years == sorted(last_5_years, reverse=True):
                insights.append("Revenue has declined for the last 5 years.")
        
        return Response({"ticker": ticker, "insights": insights}, status=status.HTTP_200_OK)

class CustomQueryAPIView(APIView):
    def post(self, request):
        ticker = request.data.get("ticker")
        metrics = request.data.get("metrics", [])
        periods = request.data.get("periods", [])
        
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        company = Company.objects.filter(ticker=ticker).first()
        if not company:
            return Response({"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        
        data = {}
        for metric in metrics:
            data[metric] = {}
            for period in periods:
                fm = FinancialMetric.objects.filter(period__company=company, name=metric, period__year=period).first()
                data[metric][period] = fm.value if fm else None
        
        return Response({"ticker": ticker, "data": data}, status=status.HTTP_200_OK)

class IndustryComparisonAPIView(APIView):
    def get(self, request):
        try:
            industries = request.GET.get("industries", "").split(',')
            metric = request.GET.get("metric", "revenue")
            
            # Read industry mappings from Excel
            df = pd.read_excel(os.path.join('sec_app', 'data', 'stocks_perf_data.xlsx'))
            
            # Create industry-ticker mapping
            industry_tickers = {}
            for industry in industries:
                industry_tickers[industry] = df[df['Industry'] == industry]['Symbol'].tolist()
            
            # Get all metrics for these companies
            all_metrics = []
            for industry, tickers in industry_tickers.items():
                metrics = FinancialMetric.objects.filter(
                    company__ticker__in=tickers,
                    metric_name=metric
                ).values('period__period').annotate(
                    avg_value=Avg('value')  # Calculate average instead of sum
                ).order_by('period__period')
                
                # Add to all metrics
                for m in metrics:
                    all_metrics.append({
                        'period': m['period__period'],
                        'industry': industry,
                        'value': float(m['avg_value'] or 0)  # Use average value
                    })
            
            # Get unique periods
            all_periods = sorted(set(m['period'] for m in all_metrics))
            
            # Format data for chart
            chart_data = []
            for period in all_periods:
                data_point = {'period': period}
                for industry in industries:
                    avg = next(
                        (m['value'] for m in all_metrics 
                         if m['period'] == period and m['industry'] == industry),
                        0
                    )
                    data_point[f"{industry}_total"] = avg  # Keep the key name for frontend compatibility
                chart_data.append(data_point)
            
            return Response({
                "industries": industries,
                "comparisons": chart_data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class FinancialMetricsAPIView(APIView):
    def get(self, request):
        ticker = request.GET.get("company__ticker")
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        metrics = FinancialMetric.objects.filter(company__ticker=ticker)
        
        
        if not metrics.exists():
            return Response({"error": "No financial data available for this ticker."}, status=status.HTTP_404_NOT_FOUND)
        
        data = [
            {
                "id": metric.id,
                "company": metric.company.id,
                "period": metric.period.id,
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "xbrl_tag": metric.xbrl_tag,
                "company_name": metric.company.name,
                "company_ticker": metric.company.ticker,
            }
            for metric in metrics
        ]
        
        return Response(data, status=status.HTTP_200_OK)

class IndustryAPIView(APIView):
    def get(self, request):
        try:
            # Get companies we have data for
            companies_with_data = Company.objects.values_list('ticker', flat=True)
            
            # Read the Excel file
            file_path = os.path.join('sec_app', 'data', 'stocks_perf_data.xlsx')
            df = pd.read_excel(file_path)
            
            # Filter DataFrame to only include companies we have data for
            df = df[df['Symbol'].isin(companies_with_data)]
            
            # Get industries that have companies with data
            industries = df[['Industry', 'Symbol']].dropna().groupby('Industry')['Symbol'].apply(list).to_dict()
            
            return Response({
                "industries": [
                    {
                        "name": industry,
                        "companies": companies
                    }
                    for industry, companies in industries.items()
                    if len(companies) > 0  # Only include industries with companies
                ]
            })
        except Exception as e:
            return Response(
                {"error": "Failed to fetch industries"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class BoxPlotDataAPIView(APIView):
    def get(self, request):
        metrics = request.GET.getlist('metric[]')
        period = request.GET.get('period')
        industry = request.GET.get('industry')

        if metrics and period:
            try:
                file_path = os.path.join('sec_app', 'data', 'stocks_perf_data.xlsx')
                df = pd.read_excel(file_path)
                
                if industry:
                    industry_companies = df[df['Industry'] == industry]['Symbol'].tolist()
                    
                    current_year = 2024
                    period_str = ""
                    if period == '1Y':
                        period_str = str(current_year)
                    elif period == '2Y':
                        period_str = f"{current_year-1}-{str(current_year)[-2:]}"
                    elif period == '3Y':
                        period_str = f"{current_year-2}-{str(current_year)[-2:]}"
                    elif period == '4Y':
                        period_str = f"{current_year-3}-{str(current_year)[-2:]}"
                    elif period == '5Y':
                        period_str = f"{current_year-4}-{str(current_year)[-2:]}"
                    elif period == '10Y':
                        period_str = f"{current_year-9}-{str(current_year)[-2:]}"
                    elif period == '15Y':
                        period_str = f"{current_year-14}-{str(current_year)[-2:]}"
                    elif period == '20Y':
                        period_str = f"{current_year-19}-{str(current_year)[-2:]}"

                    # Process each metric
                    result_data = {}
                    result_companies = {}
                    
                    for metric in metrics:
                        metrics_query = FinancialMetric.objects.filter(
                            metric_name=metric,
                            period__period__contains=period_str,
                            company__ticker__in=industry_companies
                        ).select_related('company').order_by('company__ticker')

                        values = []
                        company_names = []
                        for metric_obj in metrics_query:
                            if metric_obj.value is not None:
                                values.append(float(metric_obj.value))
                                company_names.append(metric_obj.company.ticker)

                        # Sort and store data for this metric
                        if values and company_names:
                            zipped = sorted(zip(company_names, values), key=lambda x: x[0])
                            company_names, values = zip(*zipped)
                            result_data[metric] = list(values)
                            result_companies[metric] = list(company_names)
                    
                    data = {
                        "values": result_data,
                        "companyNames": result_companies
                    }
                    return Response(data, status=status.HTTP_200_OK)
                
                return Response({"error": "Industry parameter required"}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
class AggregatedDataAPIView(APIView):
    def get(self, request):
        tickers = request.GET.get("tickers", "").split(',')
        metric = request.GET.get("metric", "Revenue")  # Default to "Revenue" with capital R
        period = request.GET.get("period", "1Y").strip('"')

        if not tickers or not tickers[0]:
            return Response({"error": "Tickers are required."}, status=400)

        print(f"Fetching data for tickers: {tickers}, metric: {metric}, period: {period}")

        # Capitalize first letter of metric to match database
        metric = metric[0].upper() + metric[1:] if metric else ""

        # Check if companies exist
        companies = Company.objects.filter(ticker__in=tickers)
        print(f"Found companies in DB: {list(companies.values_list('ticker', flat=True))}")

        # Get metrics based on period type
        metrics = FinancialMetric.objects.filter(
            company__ticker__in=tickers,
            metric_name=metric
        ).select_related('period')

        print(f"Found {metrics.count()} total metrics")
        print(f"SQL Query: {metrics.query}")

        # Filter metrics based on period type
        if period == '1Y':
            metrics = metrics.filter(period__period__regex=r'^\d{4}$')
        else:
            year_span = int(period.replace('Y', ''))
            metrics = metrics.filter(
                period__period__regex=fr'^\d{{4}}-\d{{2}}$',
                period__period__contains='-'
            )

        print(f"After period filtering: {metrics.count()} metrics")
        
        # Group by period and calculate aggregates
        aggregated_data = []
        for ticker in tickers:
            ticker_metrics = metrics.filter(company__ticker=ticker)
            print(f"\nProcessing {ticker}:")
            print(f"Found {ticker_metrics.count()} metrics")
            if ticker_metrics.exists():
                print("Sample periods:", list(ticker_metrics.values_list('period__period', flat=True))[:5])
            
            for metric_obj in ticker_metrics:
                try:
                    value = float(metric_obj.value) if metric_obj.value is not None else None
                    period_str = metric_obj.period.period
                    print(f"Adding data point: {ticker}, {period_str}, {value}")
                    
                    aggregated_data.append({
                        "name": period_str,
                        "ticker": ticker,
                        "value": value
                    })
                except Exception as e:
                    print(f"Error processing metric: {str(e)}")

        # Sort data chronologically
        aggregated_data.sort(key=lambda x: x['name'])

        if not aggregated_data:
            print("No data was aggregated")
            
        return Response(aggregated_data, status=200)
@api_view(['GET'])
def get_available_metrics(request):
    try:
        company_ticker = request.GET.get('company__ticker', None)

        if company_ticker:
            company = Company.objects.filter(ticker=company_ticker).first()
            if not company:
                return Response({"metrics": []})
            
            metrics_qs = FinancialMetric.objects.filter(company=company).values_list('metric_name', flat=True).distinct()
        else:
            metrics_qs = FinancialMetric.objects.values_list('metric_name', flat=True).distinct()

        # Convert to set to guarantee uniqueness, then back to sorted list
        unique_metrics = sorted(set(metrics_qs))

        return Response({"metrics": unique_metrics})
    
    except Exception as e:
        return Response({"error": f"Failed to fetch metrics: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def check_company(request, ticker):
    try:
        company = Company.objects.get(ticker=ticker)
        metrics_count = FinancialMetric.objects.filter(company=company).count()
        
        if metrics_count == 0:
            return Response(
                {"error": f"No financial data available for {ticker}"}, 
                status=404
            )
            
        return Response({
            "ticker": company.ticker,
            "name": company.name,
            "metrics_count": metrics_count
        })
    except Company.DoesNotExist:
        return Response(
            {"error": f"Company {ticker} not found"}, 
            status=404
        )