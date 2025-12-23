# data_importer/api_views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import uuid
import logging

from ..models import FinancialFile, ImportJob
from ..serializers import (
    FinancialFileSerializer, ImportJobSerializer,
    FileUploadSerializer, ImportStartSerializer,
    ImportStatusResponseSerializer
)
from ..services.data_integration_service import import_financial_data
from ..analyzers.excel_structure_analyzer import ExcelStructureAnalyzer
from users.models import Company, FinancialPeriod
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class FinancialFileViewSet(viewsets.ModelViewSet):
    """ViewSet for FinancialFile model"""
    
    queryset = FinancialFile.objects.all()
    serializer_class = FinancialFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter files by user's companies"""
        user = self.request.user
        return FinancialFile.objects.filter(
            company__in=user.companies.all()
        ).order_by('-uploaded_at')
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """Upload Excel file via API"""
        serializer = FileUploadSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            excel_file = serializer.validated_data['excel_file']
            company_id = serializer.validated_data['company_id']
            financial_period_id = serializer.validated_data['financial_period_id']
            
            # Get company and period
            company = Company.objects.get(id=company_id)
            financial_period = FinancialPeriod.objects.get(id=financial_period_id)
            
            # Create upload directory
            upload_dir = Path('temp_uploads')
            upload_dir.mkdir(exist_ok=True)
            
            # Save file with unique name
            file_name = f"{uuid.uuid4()}_{excel_file.name}"
            file_path = upload_dir / file_name
            
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            # Analyze file structure
            analyzer = ExcelStructureAnalyzer()
            analysis_result = analyzer.analyze_excel_structure(str(file_path))
            
            if 'error' in analysis_result:
                # Delete file if analysis failed
                if file_path.exists():
                    file_path.unlink()
                return Response(
                    {'error': f"File analysis failed: {analysis_result['error']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert numpy types for JSON serialization
            def convert_numpy_types(obj):
                import numpy as np
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            safe_analysis_result = convert_numpy_types(analysis_result) if analysis_result and isinstance(analysis_result, dict) else {}
            safe_columns_mapping = convert_numpy_types(analysis_result.get('columns_mapping', {})) if analysis_result and isinstance(analysis_result, dict) else {}
            
            # Create FinancialFile record
            financial_file = FinancialFile.objects.create(
                file_name=file_name,
                original_name=excel_file.name,
                file_path=str(file_path),
                file_size=excel_file.size,
                company=company,
                financial_period=financial_period,
                uploaded_by=request.user,
                analysis_result=safe_analysis_result,
                software_type=str(safe_analysis_result.get('software_type', 'UNKNOWN')),
                confidence_score=float(safe_analysis_result.get('confidence', 0.0)),
                columns_mapping=safe_columns_mapping,
                status='ANALYZED'
            )
            
            # Create response
            response_serializer = FinancialFileSerializer(financial_file)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading file via API: {str(e)}")
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            return Response(
                {'error': f"File upload failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Get preview data for a file"""
        financial_file = self.get_object()
        
        # Check if user has access to the company
        if not financial_file.company.can_user_access(request.user):
            return Response(
                {'error': 'You do not have access to this company'},
                status=status.HTTP_403_FORBIDDEN
            )
        
            # Get imported data stats
            from ..services.data_cleanup_service import DataCleanupService
        cleanup_service = DataCleanupService(financial_file.company, financial_file.financial_period)
        imported_data_stats = cleanup_service.get_imported_data_stats()
        
        response_data = {
            'financial_file': FinancialFileSerializer(financial_file).data,
            'analysis_result': financial_file.analysis_result,
            'sample_data': financial_file.analysis_result.get('sample_data', {}),
            'issues': financial_file.analysis_result.get('issues', []),
            'imported_data_stats': imported_data_stats,
            'has_existing_data': imported_data_stats['has_data']
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def start_import(self, request, pk=None):
        """Start import process for a file"""
        financial_file = self.get_object()
        
        # Check if user has access to the company
        if not financial_file.company.can_user_access(request.user):
            return Response(
                {'error': 'You do not have access to this company'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request data
        serializer = ImportStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        delete_existing_data = serializer.validated_data.get('delete_existing_data', False)
        
        try:
            # Start import process
            result = import_financial_data(financial_file.id, delete_existing_data=delete_existing_data)
            
            if result['status'] == 'success':
                # Find the created import job
                import_job = ImportJob.objects.filter(financial_file=financial_file).latest('created_at')
                
                response_data = {
                    'message': f"Import started successfully: {result['document_count']} documents, {result['item_count']} items",
                    'job_id': import_job.job_id,
                    'delete_existing_data': delete_existing_data,
                    'result': result
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f"Import failed: {', '.join(result['errors'])}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error starting import via API: {str(e)}")
            return Response(
                {'error': f"Failed to start import: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ImportJob model (read-only)"""
    
    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter jobs by user's companies"""
        user = self.request.user
        return ImportJob.objects.filter(
            financial_file__company__in=user.companies.all()
        ).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get detailed status of an import job"""
        import_job = self.get_object()
        
        response_data = {
            'job_id': import_job.job_id,
            'status': import_job.status,
            'progress': import_job.progress,
            'current_step': import_job.current_step,
            'error_message': import_job.error_message,
            'result_data': import_job.result_data,
            'financial_file': FinancialFileSerializer(import_job.financial_file).data
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an import job"""
        import_job = self.get_object()
        
        if import_job.status in ['PENDING', 'PROCESSING']:
            import_job.cancel()
            return Response({'message': 'Import job cancelled successfully'})
        else:
            return Response(
                {'error': 'Cannot cancel job in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DataImporterAPIView(generics.GenericAPIView):
    """Main API view for data importer operations"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get data importer dashboard stats"""
        company_id = request.session.get('current_company_id')
        
        if not company_id:
            return Response(
                {'error': 'Please select a company first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Selected company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get current period
        current_period = FinancialPeriod.objects.filter(
            company=company, 
            is_active=True
        ).first()
        
        # Get statistics
        recent_files = FinancialFile.objects.filter(
            company_id=company.id
        ).order_by('-uploaded_at')[:5]
        
        active_jobs = ImportJob.objects.filter(
            financial_file__company_id=company.id,
            status__in=['PENDING', 'PROCESSING']
        ).count()
        
        total_files = FinancialFile.objects.filter(company_id=company.id).count()
        successful_imports = FinancialFile.objects.filter(
            company_id=company.id, 
            status='IMPORTED'
        ).count()
        
        response_data = {
            'company': {
                'id': company.id,
                'name': company.name
            },
            'current_period': {
                'id': current_period.id if current_period else None,
                'name': current_period.name if current_period else None
            },
            'statistics': {
                'recent_files': FinancialFileSerializer(recent_files, many=True).data,
                'active_jobs': active_jobs,
                'total_files': total_files,
                'successful_imports': successful_imports
            }
        }
        
        return Response(response_data)
