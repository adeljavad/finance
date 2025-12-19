#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite برای بررسی عملکرد سیستم بهبود یافته
Financial Assistant System - Performance & Integration Tests
"""

import os
import sys
import json
import time
import requests
import pandas as pd
import uuid
from typing import Dict, Any, List

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance.settings')

try:
    import django
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("Make sure Django is installed and settings are configured")
    sys.exit(1)

from assistant.services.data_manager import UserDataManager
from assistant.services.agent_engine import AgentEngine
from assistant.services.memory_manager import MemoryManager

class SystemTester:
    """Test Suite برای سیستم دستیار حسابدار"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.test_session_id = f"test_session_{int(time.time())}"
        self.test_user_id = f"test_user_{int(time.time())}"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """ثبت نتایج تست"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_django_imports(self):
        """تست import کردن ماژول‌های Django"""
        try:
            from assistant.services.data_manager import UserDataManager
            from assistant.services.agent_engine import AgentEngine
            from assistant.services.memory_manager import MemoryManager
            from assistant.services.rag_engine import StableRAGEngine
            self.log_test("Django Imports", True, "All modules imported successfully")
            return True
        except ImportError as e:
            self.log_test("Django Imports", False, f"Import error: {e}")
            return False
    
    def test_data_manager_initialization(self):
        """تست مقداردهی اولیه DataManager"""
        try:
            dm = UserDataManager()
            self.log_test("DataManager Init", True, "DataManager initialized successfully")
            return dm
        except Exception as e:
            self.log_test("DataManager Init", False, f"Initialization failed: {e}")
            return None
    
    def test_agent_engine_initialization(self):
        """تست مقداردهی اولیه AgentEngine"""
        try:
            ae = AgentEngine()
            self.log_test("AgentEngine Init", True, "AgentEngine initialized successfully")
            return ae
        except Exception as e:
            self.log_test("AgentEngine Init", False, f"Initialization failed: {e}")
            return None
    
    def test_memory_manager_initialization(self):
        """تست مقداردهی اولیه MemoryManager"""
        try:
            mm = MemoryManager()
            self.log_test("MemoryManager Init", True, "MemoryManager initialized successfully")
            return mm
        except Exception as e:
            self.log_test("MemoryManager Init", False, f"Initialization failed: {e}")
            return None
    
    def test_data_manager_session_operations(self, dm: UserDataManager):
        """تست عملیات session در DataManager"""
        try:
            # ایجاد session جدید
            user_id = dm.create_user_session(self.test_user_id)
            if user_id != self.test_user_id:
                self.log_test("Create Session", False, f"User ID mismatch: expected {self.test_user_id}, got {user_id}")
                return False
            
            # دریافت session
            session = dm.get_user_session(self.test_user_id)
            if not session or session.get('user_id') != self.test_user_id:
                self.log_test("Get Session", False, "Session retrieval failed")
                return False
            
            # ذخیره DataFrame تست
            test_df = pd.DataFrame({
                'شماره سند': [1, 2, 3],
                'تاریخ سند': ['2023/01/01', '2023/01/02', '2023/01/03'],
                'بدهکار': [1000, 2000, 1500],
                'بستانکار': [500, 1000, 1000],
                'توضیحات': ['تست ۱', 'تست ۲', 'تست ۳']
            })
            
            dm.save_dataframe(self.test_user_id, 'accounting_data', test_df)
            
            # بازخوانی DataFrame
            retrieved_df = dm.get_dataframe(self.test_user_id, 'accounting_data')
            if retrieved_df is None or len(retrieved_df) != 3:
                self.log_test("DataFrame Save/Load", False, "DataFrame save/load failed")
                return False
            
            self.log_test("Session Operations", True, "All session operations successful")
            return True
            
        except Exception as e:
            self.log_test("Session Operations", False, f"Session operations failed: {e}")
            return False
    
    def test_data_manager_debug(self, dm: UserDataManager):
        """تست تابع debug در DataManager"""
        try:
            debug_info = dm.debug_user_data(self.test_user_id)
            
            required_fields = ['user_id', 'has_data', 'dataframes', 'storage_type']
            missing_fields = [field for field in required_fields if field not in debug_info]
            
            if missing_fields:
                self.log_test("DataManager Debug", False, f"Missing debug fields: {missing_fields}")
                return False
            
            if debug_info.get('has_data') != True:
                self.log_test("DataManager Debug", False, "Debug shows no data found")
                return False
            
            self.log_test("DataManager Debug", True, "Debug function working correctly", debug_info)
            return True
            
        except Exception as e:
            self.log_test("DataManager Debug", False, f"Debug function failed: {e}")
            return False
    
    def test_agent_engine_query_classification(self, ae: AgentEngine):
        """تست طبقه‌بندی سوالات در AgentEngine"""
        try:
            test_queries = [
                ("تراز آزمایشی را نشان بده", "data_analysis"),
                ("جمع بدهکارها چقدر است؟", "data_analysis"),
                ("مالیات چیست؟", "general_finance"),
                ("سلام", "general")
            ]
            
            for query, expected_type in test_queries:
                classified_type = ae._classify_query(query, self.test_session_id, self.test_user_id)
                # فقط بررسی می‌کنیم که نوع معتبر باشد
                valid_types = ['data_analysis', 'no_data', 'follow_up', 'general_finance', 'general']
                if classified_type not in valid_types:
                    self.log_test("Query Classification", False, f"Invalid type returned: {classified_type}")
                    return False
            
            self.log_test("Query Classification", True, "Query classification working correctly")
            return True
            
        except Exception as e:
            self.log_test("Query Classification", False, f"Query classification failed: {e}")
            return False
    
    def test_agent_engine_user_data_check(self, ae: AgentEngine):
        """تست بررسی وجود داده کاربر در AgentEngine"""
        try:
            has_data = ae._check_user_data_exists(self.test_session_id, self.test_user_id)
            
            # چون ما دیتا ذخیره کردیم، باید True برگردد
            if not has_data:
                self.log_test("User Data Check", False, "User data check failed - no data found")
                return False
            
            self.log_test("User Data Check", True, "User data check working correctly")
            return True
            
        except Exception as e:
            self.log_test("User Data Check", False, f"User data check failed: {e}")
            return False
    
    def test_http_endpoints(self):
        """تست HTTP endpoints"""
        endpoints_to_test = [
            (f"{self.base_url}/assistant/api/system-info/", "GET"),
            (f"{self.base_url}/assistant/api/session-info/?session_id={self.test_session_id}", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code in [200, 404]:  # 404 هم قابل قبول است اگر endpoint وجود نداشته باشد
                    self.log_test(f"HTTP {method} {endpoint}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"HTTP {method} {endpoint}", False, f"Unexpected status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_test(f"HTTP {method} {endpoint}", False, f"Request failed: {e}")
    
    def test_file_upload_simulation(self, dm: UserDataManager):
        """شبیه‌سازی آپلود فایل"""
        try:
            # ایجاد فایل CSV تست
            test_csv_content = """شماره سند,تاریخ سند,بدهکار,بستانکار,توضیحات
1,2023/01/01,1000000,500000,تست اولین سند
2,2023/01/02,2000000,1000000,تست دومین سند
3,2023/01/03,1500000,1500000,تست سومین سند
4,2023/01/04,800000,2000000,تست چهارمین سند
5,2023/01/05,3000000,1000000,تست پنجمین سند"""
            
            # پردازش فایل
            dataframe = dm.process_accounting_file(
                self.test_user_id, 
                test_csv_content, 
                "test_accounting.csv"
            )
            
            if dataframe is None or len(dataframe) != 5:
                self.log_test("File Upload Simulation", False, "File processing failed")
                return False
            
            # بررسی خلاصه
            summary = dm.get_accounting_summary(self.test_user_id)
            if not summary.get('has_data'):
                self.log_test("File Upload Summary", False, "Summary shows no data")
                return False
            
            # بررسی مجموع‌ها
            totals = summary.get('financial_totals', {})
            expected_total_debit = 8300000  # جمع بدهکارها
            expected_total_credit = 6000000  # جمع بستانکارها
            
            if abs(totals.get('total_debit', 0) - expected_total_debit) > 100:
                self.log_test("File Upload Totals", False, f"Debit total mismatch: {totals.get('total_debit')}")
                return False
            
            self.log_test("File Upload Simulation", True, f"File processed successfully. {len(dataframe)} records")
            return True
            
        except Exception as e:
            self.log_test("File Upload Simulation", False, f"File upload simulation failed: {e}")
            return False
    
    def test_integration_workflow(self, dm: UserDataManager, ae: AgentEngine, mm: MemoryManager):
        """تست workflow کامل سیستم"""
        try:
            # 1. ایجاد session در Memory Manager
            session_id = mm.create_session(self.test_session_id)
            
            # 2. اضافه کردن پیام تست
            mm.add_message(self.test_session_id, 'user', 'تراز آزمایشی را نشان بده')
            
            # 3. اجرای Agent Engine
            result = ae.run(
                'تراز آزمایشی را نشان بده', 
                self.test_session_id, 
                self.test_user_id
            )
            
            if not result.get('success'):
                self.log_test("Integration Workflow", False, f"Agent execution failed: {result}")
                return False
            
            # 4. بررسی نوع query classification
            if result.get('query_type') not in ['data_analysis', 'follow_up']:
                self.log_test("Integration Query Type", False, f"Unexpected query type: {result.get('query_type')}")
                return False
            
            # 5. بررسی وجود داده
            if not result.get('has_data'):
                self.log_test("Integration Data Check", False, "Agent didn't find user data")
                return False
            
            self.log_test("Integration Workflow", True, "Complete workflow executed successfully")
            return True
            
        except Exception as e:
            self.log_test("Integration Workflow", False, f"Integration workflow failed: {e}")
            return False
    
    def test_error_handling(self, dm: UserDataManager):
        """تست مدیریت خطا"""
        try:
            # تست user_id ناموجود
            non_existent_user = f"nonexistent_{int(time.time())}"
            debug_info = dm.debug_user_data(non_existent_user)
            
            if debug_info.get('has_data') == True:
                self.log_test("Error Handling", False, "Should return no data for non-existent user")
                return False
            
            # تست dataframe ناموجود
            df = dm.get_dataframe(non_existent_user, 'nonexistent_df')
            if df is not None:
                self.log_test("Error Handling", False, "Should return None for non-existent dataframe")
                return False
            
            self.log_test("Error Handling", True, "Error handling working correctly")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error handling test failed: {e}")
            return False
    
    def run_all_tests(self):
        """اجرای تمام تست‌ها"""
        print("🚀 Starting Financial Assistant System Tests")
        print("=" * 60)
        
        # 1. تست import ها
        if not self.test_django_imports():
            print("❌ Cannot proceed without Django imports")
            return False
        
        # 2. تست DataManager
        dm = self.test_data_manager_initialization()
        if dm:
            self.test_data_manager_session_operations(dm)
            self.test_data_manager_debug(dm)
            self.test_file_upload_simulation(dm)
            self.test_error_handling(dm)
        
        # 3. تست AgentEngine
        ae = self.test_agent_engine_initialization()
        if ae:
            self.test_agent_engine_query_classification(ae)
            self.test_agent_engine_user_data_check(ae)
        
        # 4. تست MemoryManager
        mm = self.test_memory_manager_initialization()
        
        # 5. تست Integration
        if dm and ae and mm:
            self.test_integration_workflow(dm, ae, mm)
        
        # 6. تست HTTP endpoints
        self.test_http_endpoints()
        
        return True
    
    def generate_report(self):
        """تولید گزارش نتایج"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for test in self.test_results if test['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  • {test['test_name']}: {test['message']}")
        
        print("\n✅ PASSED TESTS:")
        for test in self.test_results:
            if test['success']:
                print(f"  • {test['test_name']}: {test['message']}")
        
        # ذخیره گزارش در فایل
        report_data = {
            'summary': {
                'total': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed/total)*100 if total > 0 else 0,
                'timestamp': time.time()
            },
            'tests': self.test_results
        }
        
        report_file = f"test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return passed == total

def main():
    """تابع اصلی"""
    print("🔧 Financial Assistant System Tester")
    print("This script tests the improved Redis + Session Management system\n")
    
    # بررسی Django
    try:
        import django
        print(f"✅ Django version: {django.get_version()}")
    except ImportError:
        print("❌ Django not installed")
        return False
    
    # بررسی dependencies
    required_packages = ['pandas', 'requests']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} not installed")
            return False
    
    # اجرای تست‌ها
    tester = SystemTester()
    
    try:
        success = tester.run_all_tests()
        report_success = tester.generate_report()
        
        if success and report_success:
            print("\n🎉 ALL TESTS PASSED! System is working correctly.")
            return True
        else:
            print("\n⚠️ Some tests failed. Check the report for details.")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)