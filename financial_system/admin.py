# financial_system/admin.py
from django.contrib import admin
from .models import Company, FinancialPeriod, ChartOfAccounts, DocumentHeader, DocumentItem

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'economic_code', 'national_code', 'is_active']
    search_fields = ['name', 'economic_code']

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'level', 'parent', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['code', 'name']

class DocumentItemInline(admin.TabularInline):
    model = DocumentItem
    extra = 1

@admin.register(DocumentHeader)
class DocumentHeaderAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'document_type', 'document_date', 'company', 'total_debit', 'total_credit']
    list_filter = ['document_type', 'company', 'document_date']
    inlines = [DocumentItemInline]