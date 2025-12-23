# data_importer/serializers.py
from rest_framework import serializers
from .models import FinancialFile, ImportJob
from users.models import Company, FinancialPeriod


class FinancialFileSerializer(serializers.ModelSerializer):
    """Serializer for FinancialFile model"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    financial_period_name = serializers.CharField(source='financial_period.name', read_only=True)
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    is_processable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FinancialFile
        fields = [
            'id', 'file_name', 'original_name', 'file_path', 'file_size', 'file_size_mb',
            'company', 'company_name', 'financial_period', 'financial_period_name',
            'software_type', 'confidence_score', 'columns_mapping', 'analysis_result',
            'status', 'uploaded_by', 'uploaded_by_email', 'total_documents', 'total_items',
            'validation_errors', 'uploaded_at', 'analyzed_at', 'imported_at', 'is_processable'
        ]
        read_only_fields = [
            'id', 'file_name', 'file_path', 'file_size', 'file_size_mb',
            'company_name', 'financial_period_name', 'uploaded_by_email',
            'software_type', 'confidence_score', 'columns_mapping', 'analysis_result',
            'status', 'uploaded_by', 'total_documents', 'total_items',
            'validation_errors', 'uploaded_at', 'analyzed_at', 'imported_at', 'is_processable'
        ]


class ImportJobSerializer(serializers.ModelSerializer):
    """Serializer for ImportJob model"""
    
    financial_file_name = serializers.CharField(source='financial_file.original_name', read_only=True)
    
    class Meta:
        model = ImportJob
        fields = [
            'id', 'job_id', 'financial_file', 'financial_file_name',
            'status', 'progress', 'current_step', 'result_data',
            'error_message', 'stack_trace', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'job_id', 'financial_file_name', 'status', 'progress',
            'current_step', 'result_data', 'error_message', 'stack_trace',
            'created_at', 'started_at', 'completed_at'
        ]


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload API"""
    
    excel_file = serializers.FileField(
        required=True,
        help_text="Excel file (.xlsx or .xls)"
    )
    company_id = serializers.IntegerField(
        required=True,
        help_text="ID of the company"
    )
    financial_period_id = serializers.IntegerField(
        required=True,
        help_text="ID of the financial period"
    )
    
    def validate_excel_file(self, value):
        """Validate uploaded file"""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Only Excel files with .xlsx or .xls extensions are allowed"
            )
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size should not exceed 50MB. Current size: {value.size / (1024*1024):.2f}MB"
            )
        
        return value
    
    def validate_company_id(self, value):
        """Validate company exists"""
        try:
            company = Company.objects.get(id=value)
        except Company.DoesNotExist:
            raise serializers.ValidationError(f"Company with ID {value} does not exist")
        
        # Check if user has access to this company
        request = self.context.get('request')
        if request and not company.can_user_access(request.user):
            raise serializers.ValidationError("You don't have access to this company")
        
        return value
    
    def validate_financial_period_id(self, value):
        """Validate financial period exists"""
        try:
            FinancialPeriod.objects.get(id=value)
        except FinancialPeriod.DoesNotExist:
            raise serializers.ValidationError(f"Financial period with ID {value} does not exist")
        
        return value


class ImportStartSerializer(serializers.Serializer):
    """Serializer for starting import process"""
    
    delete_existing_data = serializers.BooleanField(
        default=False,
        help_text="Whether to delete existing data before import"
    )


class ImportStatusResponseSerializer(serializers.Serializer):
    """Serializer for import status response"""
    
    job_id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    current_step = serializers.CharField()
    error_message = serializers.CharField(allow_null=True)
    result_data = serializers.DictField(allow_null=True)
    financial_file = FinancialFileSerializer(read_only=True)


class HierarchicalUploadSerializer(serializers.Serializer):
    """Serializer for hierarchical file upload with two models support"""
    
    excel_file = serializers.FileField(
        required=True,
        help_text="Excel file (.xlsx or .xls)"
    )
    company_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the company (optional for generic upload)"
    )
    financial_period_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the financial period (optional for generic upload)"
    )
    
    # Optional column mapping for hierarchical structure
    main_account_code_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for main account code"
    )
    main_account_name_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for main account name"
    )
    sub_account_code_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for sub account code"
    )
    sub_account_name_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for sub account name"
    )
    detail_account_code_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for detail account code"
    )
    detail_account_name_column = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Column name for detail account name"
    )
    
    def validate_excel_file(self, value):
        """Validate uploaded file"""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Only Excel files with .xlsx or .xls extensions are allowed"
            )
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size should not exceed 50MB. Current size: {value.size / (1024*1024):.2f}MB"
            )
        
        return value
    
    def validate_company_id(self, value):
        """Validate company exists if provided"""
        if value is None:
            return value
        
        try:
            from users.models import Company
            company = Company.objects.get(id=value)
        except Company.DoesNotExist:
            raise serializers.ValidationError(f"Company with ID {value} does not exist")
        
        # Check if user has access to this company
        request = self.context.get('request')
        if request and not company.can_user_access(request.user):
            raise serializers.ValidationError("You don't have access to this company")
        
        return value
    
    def validate_financial_period_id(self, value):
        """Validate financial period exists if provided"""
        if value is None:
            return value
        
        try:
            from users.models import FinancialPeriod
            FinancialPeriod.objects.get(id=value)
        except FinancialPeriod.DoesNotExist:
            raise serializers.ValidationError(f"Financial period with ID {value} does not exist")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        company_id = data.get('company_id')
        financial_period_id = data.get('financial_period_id')
        
        # اگر یکی از company_id یا financial_period_id ارائه شده، دیگری هم باید ارائه شود
        if (company_id is not None and financial_period_id is None) or \
           (company_id is None and financial_period_id is not None):
            raise serializers.ValidationError(
                "Both company_id and financial_period_id must be provided together, or both should be omitted"
            )
        
        return data


class StandardAccountChartSerializer(serializers.ModelSerializer):
    """Serializer for StandardAccountChart model"""
    
    parent_name = serializers.CharField(source='parent.standard_name', read_only=True)
    full_path = serializers.CharField(read_only=True)
    is_leaf = serializers.BooleanField(read_only=True)
    
    class Meta:
        from .models import StandardAccountChart
        model = StandardAccountChart
        fields = [
            'id', 'standard_code', 'standard_name', 'account_type', 'level',
            'parent', 'parent_name', 'is_active', 'description', 'natural_balance',
            'full_path', 'is_leaf', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_path', 'is_leaf', 'created_at', 'updated_at']


class CompanyAccountMappingSerializer(serializers.ModelSerializer):
    """Serializer for CompanyAccountMapping model"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    standard_main_code_display = serializers.CharField(source='standard_main_code.standard_code', read_only=True)
    standard_main_name_display = serializers.CharField(source='standard_main_code.standard_name', read_only=True)
    standard_sub_code_display = serializers.CharField(source='standard_sub_code.standard_code', read_only=True, allow_null=True)
    standard_sub_name_display = serializers.CharField(source='standard_sub_code.standard_name', read_only=True, allow_null=True)
    standard_detail_code_display = serializers.CharField(source='standard_detail_code.standard_code', read_only=True, allow_null=True)
    standard_detail_name_display = serializers.CharField(source='standard_detail_code.standard_name', read_only=True, allow_null=True)
    company_full_code = serializers.CharField(read_only=True)
    standard_full_code = serializers.CharField(read_only=True)
    
    class Meta:
        from .models import CompanyAccountMapping
        model = CompanyAccountMapping
        fields = [
            'id', 'company', 'company_name',
            'company_main_code', 'company_main_name',
            'company_sub_code', 'company_sub_name',
            'company_detail_code', 'company_detail_name',
            'standard_main_code', 'standard_main_code_display', 'standard_main_name_display',
            'standard_sub_code', 'standard_sub_code_display', 'standard_sub_name_display',
            'standard_detail_code', 'standard_detail_code_display', 'standard_detail_name_display',
            'is_active', 'confidence_score', 'mapping_type',
            'created_by', 'created_at', 'updated_at',
            'company_full_code', 'standard_full_code'
        ]
        read_only_fields = [
            'id', 'company_name', 'standard_main_code_display', 'standard_main_name_display',
            'standard_sub_code_display', 'standard_sub_name_display',
            'standard_detail_code_display', 'standard_detail_name_display',
            'company_full_code', 'standard_full_code', 'created_at', 'updated_at'
        ]


class RawFinancialDataSerializer(serializers.ModelSerializer):
    """Serializer for RawFinancialData model"""
    
    financial_file_name = serializers.CharField(source='financial_file.original_name', read_only=True)
    net_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    has_hierarchy = serializers.BooleanField(read_only=True)
    
    class Meta:
        from .models import RawFinancialData
        model = RawFinancialData
        fields = [
            'id', 'financial_file', 'financial_file_name',
            'main_account_code', 'main_account_name',
            'sub_account_code', 'sub_account_name',
            'detail_account_code', 'detail_account_name',
            'document_number', 'document_date', 'description',
            'debit_amount', 'credit_amount', 'net_amount',
            'row_index', 'imported', 'mapping_applied',
            'standard_main_code', 'standard_main_name',
            'standard_sub_code', 'standard_sub_name',
            'standard_detail_code', 'standard_detail_name',
            'has_hierarchy', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'financial_file_name', 'net_amount', 'has_hierarchy',
            'created_at', 'updated_at'
        ]


class BulkMappingImportSerializer(serializers.Serializer):
    """Serializer for bulk mapping import from Excel"""
    
    mapping_file = serializers.FileField(
        required=True,
        help_text="Excel file containing mapping data"
    )
    company_id = serializers.IntegerField(
        required=True,
        help_text="ID of the company"
    )
    mapping_type = serializers.ChoiceField(
        choices=[('MANUAL', 'دستی'), ('BULK_IMPORT', 'وارد کردن دسته‌ای')],
        default='BULK_IMPORT',
        help_text="Type of mapping"
    )
    
    def validate_mapping_file(self, value):
        """Validate mapping file"""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Only Excel files with .xlsx or .xls extensions are allowed"
            )
        
        return value
    
    def validate_company_id(self, value):
        """Validate company exists"""
        try:
            from users.models import Company
            Company.objects.get(id=value)
        except Company.DoesNotExist:
            raise serializers.ValidationError(f"Company with ID {value} does not exist")
        
        return value
