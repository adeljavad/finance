#!/usr/bin/env python3
"""
Simple test for the help system
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from financial_system.help_system import help_system
    print("✅ Help system imported successfully!")
    
    # Test basic functionality
    print("\n🔍 Testing tool discovery...")
    tools_count = len(help_system.tools_registry)
    print(f"✅ Discovered {tools_count} tools")
    
    # Test help responses
    print("\n📋 Testing help responses...")
    
    help_responses = [
        ("general", ""),
        ("tools_list", ""),
        ("tool_detail", "current_ratio_calculation")
    ]
    
    for help_type, query in help_responses:
        response = help_system.generate_help_response(help_type, query)
        print(f"✅ {help_type} help: {len(response)} characters")
        print(f"   Preview: {response[:100]}...")
    
    print("\n🎉 Help system is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
