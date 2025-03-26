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
from django.db.models import Avg
from .models.query import Query
from .serializer import *
from rest_framework.decorators import api_view
from .api_client import fetch_financial_data
from .utils import *
from django.http import JsonResponse
import logging
import requests
from django.conf import settings

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
        ticker = request.GET.get("ticker")
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        company = Company.objects.filter(ticker=ticker).first()
        if not company:
            return Response({"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        
        revenue_metrics = FinancialMetric.objects.filter(company=company, metric_name="Revenue")
        profit_metrics = FinancialMetric.objects.filter(company=company, metric_name="Profit")
        
        logger.info(f"Revenue metrics for {ticker}: {list(revenue_metrics)}")
        logger.info(f"Profit metrics for {ticker}: {list(profit_metrics)}")
        
        data = []
        # Use profit metrics as the base since revenue metrics are missing
        for profit in profit_metrics:
            try:
                period_name = profit.period.period
                revenue_value = revenue_metrics.filter(period=profit.period).first()

                logger.info(f"Processing period: {period_name}, Revenue: {revenue_value}, Profit: {profit.value}")

                data.append({
                    "period": period_name,
                    "revenue": revenue_value.value if revenue_value else 0,  # Default to 0 if missing
                    "profit": profit.value,
                })
            except Exception as e:
                logger.error(f"Error processing metrics for period {profit.period}: {str(e)}")
                return Response({"error": "Error processing financial metrics."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"Data returned for {ticker}: {data}")
        return Response({"ticker": ticker, "metrics": data}, status=status.HTTP_200_OK)

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
        ticker = request.GET.get("ticker")
        if not ticker:
            return Response({"error": "Ticker is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        company = Company.objects.filter(ticker=ticker).first()
        if not company or not company.industry:
            return Response({"error": "Company or industry data not found."}, status=status.HTTP_404_NOT_FOUND)
        
        comparisons = []
        for metric in ["Revenue Growth", "Net Profit Margin"]:
            company_metric = FinancialMetric.objects.filter(period__company=company, name=metric).aggregate(Avg("value"))
            industry_metric = FinancialMetric.objects.filter(period__company__industry=company.industry, name=metric).aggregate(Avg("value"))
            comparisons.append({
                "metric": metric,
                "company": company_metric["value__avg"],
                "industry_avg": industry_metric["value__avg"]
            })
        
        return Response({"ticker": ticker, "industry": company.industry, "comparisons": comparisons}, status=status.HTTP_200_OK)

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
