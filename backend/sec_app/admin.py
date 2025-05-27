from django.contrib import admin
from .models.company import Company
from .models.period import FinancialPeriod
from .models.metric import FinancialMetric
from .models.filling import FilingDocument
from .models.filing import Filing
from .models.analysis import SentimentAnalysis
from .models.query import Query
from .models.mapping import MetricMapping
from .models.chatlog import ChatLog
# Register your models here.

@admin.register(ChatLog)
class ChatlogAdmin(admin.ModelAdmin):
    list_display = ('question','answer')

@admin.register(Filing)
class FilingAdmin(admin.ModelAdmin):
    list_display = ('company', 'form', 'filing_date', 'accession_number')
    search_fields = ('company__name', 'form', 'accession_number')
    list_filter = ('company__sector', 'company__industry')


@admin.register(MetricMapping)
class MetricMappingAdmin(admin.ModelAdmin):
    list_display = ('xbrl_tag', 'standard_name', 'priority')
    search_fields = ('xbrl_tag', 'standard_name')
    list_filter = ('priority',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticker', 'sector', 'industry')
    search_fields = ('name', 'ticker')
    list_filter = ('sector', 'industry')

@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = ('company', 'period', 'start_date', 'end_date', 'filing_date')
    search_fields = ('company__name', 'period')
    list_filter = ('company__sector', 'company__industry')

@admin.register(FinancialMetric)
class FinancialMetricAdmin(admin.ModelAdmin):
    list_display = ('period', 'metric_name', 'value', 'unit')
    search_fields = ('xbrl_tag', 'metric_name')
    list_filter = ('xbrl_tag', 'period__company__industry')

@admin.register(FilingDocument)
class FilingDocumentAdmin(admin.ModelAdmin):
    list_display = ('company', 'period', 'section_name')
    search_fields = ('company__name', 'period__period')
    list_filter = ('company__sector', 'company__industry')

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('document', 'sentiment_score', 'sentiment_label')
    search_fields = ('document__company__name', 'document__period__period')
    list_filter = ('document__company__sector', 'document__company__industry')

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'timestamp')
    search_fields = ('query',)
    list_filter = ('timestamp',)
    







