from rest_framework import serializers
from .models.company import Company
from .models.analysis import SentimentAnalysis
from .models.period import FinancialPeriod
from .models.filling import FilingDocument
from .models.metric import FinancialMetric
from .models.query import Query


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'ticker', 'cik', 'sector', 'industry']

class FinancialPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPeriod
        fields = ['id', 'company', 'period', 'period_type', 'start_date', 'end_date', 'filing_date']


class FilingDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilingDocument
        fields = ['id', 'company', 'period', 'section_name', 'content']


class FinancialMetricSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker', read_only=True)

    class Meta:
        model = FinancialMetric
        fields = ['id','company', 'period', 'metric_name', 'value', 'unit', 'xbrl_tag', 'company_name', 'company_ticker']


class SentimentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentAnalysis
        fields = '__all__'  

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = '__all__'










