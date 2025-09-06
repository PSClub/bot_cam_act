#!/usr/bin/env python3
"""
Test script to evaluate the optimized changes made to browser_actions.py:
1. Post-midnight calendar advancement optimization
2. Back navigation optimization (browser.go_back() instead of button search)
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need for testing structure
# from browser_actions import get_timestamp  # We'll define our own for testing
from datetime import datetime

class MockSession:
    """Mock session for testing without actual session manager"""
    def __init__(self):
        self.messages = []
    
    def log_message(self, message):
        self.messages.append(message)
        print(f"[SESSION] {message}")

def get_timestamp():
    """Simple timestamp function for testing"""
    return datetime.now().strftime("%H:%M:%S")

class OptimizationTester:
    def __init__(self):
        self.test_results = []
    
    def log_test_result(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': get_timestamp()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
    
    async def test_post_midnight_advancement_structure(self):
        """Test the structure and logic of the optimized post_midnight_calendar_advancement function"""
        print(f"\n{get_timestamp()} 🧪 Testing optimized post_midnight_calendar_advancement structure...")
        
        try:
            # Read the function source to verify optimizations
            with open('browser_actions.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for optimization indicators
            function_start = content.find('async def post_midnight_calendar_advancement')
            if function_start == -1:
                self.log_test_result("Function exists", False, "post_midnight_calendar_advancement not found")
                return
            
            function_end = content.find('\nasync def', function_start + 1)
            if function_end == -1:
                function_end = len(content)
            
            function_code = content[function_start:function_end]
            
            # Test 1: Check for optimized timeout (500ms instead of 1000ms)
            has_fast_timeout = 'timeout=500' in function_code
            self.log_test_result(
                "Fast date visibility check (500ms)", 
                has_fast_timeout,
                "Should use 500ms timeout for quick date checks"
            )
            
            # Test 2: Check for removal of fixed sleep delays
            has_no_sleep = 'asyncio.sleep(' not in function_code
            self.log_test_result(
                "No fixed sleep delays", 
                has_no_sleep,
                "Should not have asyncio.sleep() calls that add unnecessary delays"
            )
            
            # Test 3: Check for continuous while loop instead of attempt-based
            has_while_loop = 'while (' in function_code and 'total_seconds()' in function_code
            self.log_test_result(
                "Continuous time-based loop", 
                has_while_loop,
                "Should use while loop with time check instead of attempt counter"
            )
            
            # Test 4: Check for increased timeouts (15000ms)
            has_increased_timeouts = 'timeout=15000' in function_code
            self.log_test_result(
                "Increased click/load timeouts", 
                has_increased_timeouts,
                "Should have 15 second timeouts for clicks and page loads"
            )
            
            # Test 5: Check for immediate page reload on error
            has_immediate_reload = 'page.reload(wait_until="domcontentloaded"' in function_code
            self.log_test_result(
                "Immediate error recovery", 
                has_immediate_reload,
                "Should reload page immediately on errors"
            )
            
        except Exception as e:
            self.log_test_result("Function structure analysis", False, f"Error: {e}")
    
    async def test_back_navigation_optimization(self):
        """Test the back navigation optimization in add_slot_to_basket"""
        print(f"\n{get_timestamp()} 🧪 Testing back navigation optimization...")
        
        try:
            # Read the function source to verify back navigation changes
            with open('browser_actions.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the book_slot function (contains the navigation logic)
            function_start = content.find('async def book_slot')
            if function_start == -1:
                self.log_test_result("book_slot exists", False, "Function not found")
                return
            
            # Find the navigation section
            nav_section_start = content.find('# Navigate back to calendar', function_start)
            if nav_section_start == -1:
                self.log_test_result("Navigation section exists", False, "Navigation section not found")
                return
            
            nav_section_end = content.find('\n        except', nav_section_start)
            if nav_section_end == -1:
                nav_section_end = content.find('\n    except', nav_section_start)
            
            nav_code = content[nav_section_start:nav_section_end] if nav_section_end != -1 else content[nav_section_start:nav_section_start+1000]
            
            # Test 1: Check that back button search is removed
            no_back_selectors = 'back_selectors' not in nav_code
            self.log_test_result(
                "Back button search removed", 
                no_back_selectors,
                "Should not search for back button selectors"
            )
            
            # Test 2: Check for direct browser back navigation
            has_direct_back = 'page.go_back()' in nav_code and 'browser back navigation' in nav_code
            self.log_test_result(
                "Direct browser back navigation", 
                has_direct_back,
                "Should use page.go_back() directly"
            )
            
            # Test 3: Check that selector loop is removed
            no_selector_loop = 'for selector in' not in nav_code
            self.log_test_result(
                "No selector loop", 
                no_selector_loop,
                "Should not loop through back button selectors"
            )
            
            # Test 4: Check for simplified logic
            simplified = nav_code.count('try:') <= 1  # Should have minimal try blocks
            self.log_test_result(
                "Simplified navigation logic", 
                simplified,
                "Should have simplified logic without complex nested tries"
            )
            
        except Exception as e:
            self.log_test_result("Back navigation analysis", False, f"Error: {e}")
    
    async def test_function_compatibility(self):
        """Test that the optimized functions maintain their expected interfaces"""
        print(f"\n{get_timestamp()} 🧪 Testing function compatibility...")
        
        try:
            # Check function definition exists and has correct structure
            with open('browser_actions.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check function signature in source
            function_def = "async def post_midnight_calendar_advancement(page, target_date_str, slot_details, session=None):"
            has_correct_signature = function_def in content
            
            self.log_test_result(
                "post_midnight_calendar_advancement signature", 
                has_correct_signature,
                "Function should have correct parameter signature"
            )
            
            # Check that function is properly async
            is_async = "async def post_midnight_calendar_advancement" in content
            self.log_test_result(
                "Function is async", 
                is_async,
                "Function should be defined as async"
            )
            
        except Exception as e:
            self.log_test_result("Function compatibility", False, f"Error: {e}")
    
    async def test_performance_characteristics(self):
        """Test that the optimizations should improve performance characteristics"""
        print(f"\n{get_timestamp()} 🧪 Testing performance characteristics...")
        
        try:
            with open('browser_actions.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count potential delay sources in the optimized function
            post_midnight_start = content.find('async def post_midnight_calendar_advancement')
            post_midnight_end = content.find('\nasync def', post_midnight_start + 1)
            if post_midnight_end == -1:
                post_midnight_end = len(content)
            
            function_code = content[post_midnight_start:post_midnight_end]
            
            # Count sleep calls (should be 0)
            sleep_count = function_code.count('asyncio.sleep(')
            self.log_test_result(
                "Zero sleep delays", 
                sleep_count == 0,
                f"Found {sleep_count} sleep calls (should be 0)"
            )
            
            # Count timeout values and check they're appropriate
            short_timeouts = function_code.count('timeout=500')  # Quick checks
            long_timeouts = function_code.count('timeout=15000')  # Action timeouts
            
            has_optimized_timeouts = short_timeouts >= 1 and long_timeouts >= 1
            self.log_test_result(
                "Optimized timeout strategy", 
                has_optimized_timeouts,
                f"Short timeouts: {short_timeouts}, Long timeouts: {long_timeouts}"
            )
            
            # Check for efficient loop structure
            efficient_loop = 'while (' in function_code and 'datetime.now(' in function_code
            self.log_test_result(
                "Efficient loop structure", 
                efficient_loop,
                "Should use time-based while loop for efficiency"
            )
            
        except Exception as e:
            self.log_test_result("Performance characteristics", False, f"Error: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{get_timestamp()} 📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
        
        print("\n" + "=" * 50)

async def main():
    """Run all optimization tests"""
    print(f"{get_timestamp()} 🚀 Starting optimization evaluation tests...")
    
    tester = OptimizationTester()
    
    # Run all tests
    await tester.test_post_midnight_advancement_structure()
    await tester.test_back_navigation_optimization()
    await tester.test_function_compatibility()
    await tester.test_performance_characteristics()
    
    # Print summary
    tester.print_summary()
    
    return len([r for r in tester.test_results if not r['passed']]) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
