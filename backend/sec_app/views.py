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
from django.db.models import Avg, Sum
from .models.query import Query
from .serializer import *
from rest_framework.decorators import api_view
from .api_client import fetch_financial_data
from .utils import *
from django.http import JsonResponse
import logging
import requests
from django.conf import settings
import pandas as pd
import os

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_sec_data(request):
    return Response({"message": "Hello, world!"})

@api_view(['GET'])
def extract_financials(request):
    ticker = request.GET.get('ticker', 'AAPL')
    logger.info(f"Fetching financial data for {ticker}")
    
    data = fetch_financial_data(ticker)
    if data and data.get('filings'):
        try:
            # Log sample filing details
            sample_filing = data['filings'][0]
            logger.info(f"Sample filing type: {sample_filing.get('formType')}")
            logger.info(f"Sample filing date: {sample_filing.get('filedAt')}")
            logger.info(f"Sample docs: {sample_filing.get('documentFormatFiles')}")
            
            # Check if the data has the expected structure for save_financial_data_to_db
            logger.info(f"Data structure: ticker={data.get('ticker')}, cik={data.get('cik')}")
            logger.info(f"First filing data keys: {list(sample_filing.keys())}")
            
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
            logger.error(f"Error saving data: {str(e)}")
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
        
        logger.info(f"Testing API with URL: {api_url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {payload}")
        
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
            
            # Add logging to debug
            logger.info(f"Fetching data for tickers: {tickers}, metric: {metric}")
            
            for ticker in tickers:
                company = Company.objects.filter(ticker=ticker).first()
                if company:
                    # Log the query parameters
                    logger.info(f"Querying for company: {company}, metric: {metric}")
                    
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
            logger.info(f"Returning data with {len(period_data)} periods")
            
            return Response({
                "tickers": tickers,
                "metrics": period_data,
                "selected_metric": metric
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in ChartDataAPIView: {str(e)}")
            return Response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def get_available_metrics(request):
        metrics = FinancialMetric.objects.values_list('metric_name', flat=True).distinct()
        logger.info(f"Available metrics in database: {list(metrics)}")
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
                logger.info(f"Industry {industry} has tickers: {industry_tickers[industry]}")
            
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
            
            logger.info(f"Returning chart data: {chart_data[:2]}")  # Log first two points
            
            return Response({
                "industries": industries,
                "comparisons": chart_data
            })
            
        except Exception as e:
            logger.error(f"Error in IndustryComparisonAPIView: {str(e)}")
            logger.error("Full traceback:", exc_info=True)
            return Response({"error": str(e)}, status=500)

class FinancialMetricsAPIView(APIView):
    def get(self, request):
        ticker = request.GET.get("company__ticker")
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        metrics = FinancialMetric.objects.filter(company__ticker=ticker)
        
        logger.info(f"Metrics for {ticker}: {list(metrics)}")
        
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
        
        logger.info(f"Data returned for {ticker}: {data}")
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
            logger.error(f"Error fetching industries: {str(e)}")
            return Response(
                {"error": "Failed to fetch industries"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class BoxPlotDataAPIView(APIView):
    def get(self, request):
        metrics = request.GET.getlist('metric[]')  # Changed to handle multiple metrics
        period = request.GET.get('period')
        industry = request.GET.get('industry')

        logger.info(f"Querying for metrics: {metrics}, period: {period}, industry: {industry}")

        if metrics and period:
            try:
                file_path = os.path.join('sec_app', 'data', 'stocks_perf_data.xlsx')
                df = pd.read_excel(file_path)
                
                if industry:
                    industry_companies = df[df['Industry'] == industry]['Symbol'].tolist()
                    logger.info(f"Companies in {industry}: {industry_companies}")
                    
                    current_year = 2024
                    if period == '1Y':
                        year = str(current_year - 1)
                    elif period == '2Y':
                        year = str(current_year - 2)
                    else:
                        year = str(current_year - 1)

                    # Process each metric
                    result_data = {}
                    result_companies = {}
                    
                    for metric in metrics:
                        metrics_query = FinancialMetric.objects.filter(
                            metric_name=metric,
                            period__period__contains=year,
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
                logger.error(f"Error fetching data: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
class AggregatedDataAPIView(APIView):
    def get(self, request):
        tickers = request.GET.get("tickers", "").split(',')
        metric = request.GET.get("metric", "revenue")
        period = request.GET.get("period", "1Y").strip('"')

        if not tickers or not tickers[0]:
            return Response({"error": "Tickers are required."}, status=400)

        # Add debug logging
        print(f"Fetching data for tickers: {tickers}, metric: {metric}, period: {period}")

        if period == "2Y":
            intervals = [(2015, 2016), (2017, 2018), (2019, 2020), (2021, 2022), (2023, 2024)]
        elif period == "3Y":
            intervals = [(2015, 2017), (2018, 2020), (2021, 2023)]
        elif period == "5Y":
            intervals = [(2015, 2019), (2020, 2024)]
        elif period == "10Y":
            intervals = [(2015, 2024)]  # Single 10-year interval
        else:
            intervals = [(year, year) for year in range(2015, 2025)]

        aggregated_data = []

        for start, end in intervals:
            print(f"Querying interval: {start}-{end}")
            metrics = FinancialMetric.objects.filter(
                company__ticker__in=tickers,
                metric_name=metric,
                period__start_date__year__range=(start, end)
            )
            
            # Debug the query
            print("Query:", metrics.query)
            print("Results:", list(metrics.values()))

            metrics_dict = {m['company__ticker']: m['total'] for m in metrics.values('company__ticker').annotate(total=Sum('value'))}
            print(f"Metrics dict: {metrics_dict}")

            for ticker in tickers:
                total = metrics_dict.get(ticker, 0)
                print(f"Ticker: {ticker}, Interval: {start}-{end}, Total: {total}")
                aggregated_data.append({
                    "name": f"{start}-{end}",
                    "ticker": ticker,
                    "value": total
                })

        return Response(aggregated_data, status=200)

@api_view(['GET'])
def get_available_metrics(request):
    try:
        metrics = FinancialMetric.objects.values_list('metric_name', flat=True).distinct()
        # Remove duplicates and sort
        unique_metrics = sorted(list(set(metrics)))
        return Response({
            "metrics": unique_metrics
        })
    except Exception as e:
        logger.error(f"Error fetching available metrics: {str(e)}")
        return Response(
            {"error": "Failed to fetch metrics"}, 
            status=500
        )