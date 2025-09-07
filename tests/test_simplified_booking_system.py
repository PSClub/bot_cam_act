#!/usr/bin/env python3
"""
Comprehensive tests for the simplified booking system.
Tests the new logic where each account gets a pre-assigned slot from the BookingSchedule sheet.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets_manager import SheetsManager
from multi_session_manager import MultiSessionManager, BookingSession
from booking_orchestrator import BookingOrchestrator


class TestSheetsManager:
    """Test the updated SheetsManager functionality."""
    
    def test_read_booking_assignments(self):
        """Test reading booking assignments from the BookingSchedule sheet."""
        # Mock the worksheet reading
        mock_data = [
            {
                'Account': 'Mother',
                'Email': '1140749429@qq.com',
                'Court Number': 'Court 1',
                'Day': 'Saturday',
                'Time': '1400',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
                'Notes': 'All year'
            },
            {
                'Account': 'Father',
                'Email': 'huay43105@gmail.com',
                'Court Number': 'Court 2',
                'Day': 'Saturday',
                'Time': '1500',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/',
                'Notes': 'All year'
            }
        ]
        
        with patch.object(SheetsManager, '_read_worksheet_to_dicts', return_value=mock_data):
            sheets_manager = SheetsManager("test_sheet_id", '{"test": "credentials"}')
            
            assignments = sheets_manager.read_booking_assignments()
            
            assert len(assignments) == 2
            assert assignments[0]['Account'] == 'Mother'
            assert assignments[0]['Time'] == '1400'
            assert assignments[1]['Account'] == 'Father'
            assert assignments[1]['Time'] == '1500'


class TestMultiSessionManager:
    """Test the updated MultiSessionManager functionality."""
    
    @pytest.fixture
    def mock_sheets_manager(self):
        """Create a mock sheets manager."""
        mock_sheets = Mock(spec=SheetsManager)
        mock_sheets.read_booking_assignments.return_value = [
            {
                'Account': 'Mother',
                'Email': '1140749429@qq.com',
                'Court Number': 'Court 1',
                'Day': 'Saturday',
                'Time': '1400',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
                'Notes': 'All year'
            },
            {
                'Account': 'Father',
                'Email': 'huay43105@gmail.com',
                'Court Number': 'Court 2',
                'Day': 'Saturday',
                'Time': '1500',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/',
                'Notes': 'All year'
            },
            {
                'Account': 'Bruce',
                'Email': 'brcwood48@gmail.com',
                'Court Number': 'Court 3',
                'Day': 'Sunday',
                'Time': '1400',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/',
                'Notes': 'All year'
            }
        ]
        return mock_sheets
    
    @pytest.mark.asyncio
    async def test_initialize_sessions_with_assignments_saturday(self, mock_sheets_manager):
        """Test initializing sessions with Saturday assignments."""
        
        # Mock environment variables for passwords
        with patch.dict(os.environ, {
            'MOTHER_CAM_PASSWORD': 'mother_pass',
            'FATHER_CAM_PASSWORD': 'father_pass'
        }):
            # Mock BookingSession initialization
            with patch.object(BookingSession, 'initialize_browser', new_callable=AsyncMock) as mock_init:
                mock_init.return_value = True
                
                manager = MultiSessionManager(mock_sheets_manager)
                
                result = await manager.initialize_sessions_with_assignments('Saturday', headless=True)
                
                assert result is True
                assert len(manager.sessions) == 2
                
                # Check first session (Mother)
                mother_session = manager.sessions[0]
                assert mother_session.account_name == 'Mother'
                assert mother_session.email == '1140749429@qq.com'
                assert mother_session.court_number == 'Court 1'
                assert mother_session.assigned_time_slot == '1400'
                
                # Check second session (Father)
                father_session = manager.sessions[1]
                assert father_session.account_name == 'Father'
                assert father_session.email == 'huay43105@gmail.com'
                assert father_session.court_number == 'Court 2'
                assert father_session.assigned_time_slot == '1500'
    
    @pytest.mark.asyncio
    async def test_initialize_sessions_with_assignments_sunday(self, mock_sheets_manager):
        """Test initializing sessions with Sunday assignments."""
        
        with patch.dict(os.environ, {
            'BRUCE_CAM_PASSWORD': 'bruce_pass'
        }):
            with patch.object(BookingSession, 'initialize_browser', new_callable=AsyncMock) as mock_init:
                mock_init.return_value = True
                
                manager = MultiSessionManager(mock_sheets_manager)
                
                result = await manager.initialize_sessions_with_assignments('Sunday', headless=True)
                
                assert result is True
                assert len(manager.sessions) == 1
                
                # Check Bruce's session
                bruce_session = manager.sessions[0]
                assert bruce_session.account_name == 'Bruce'
                assert bruce_session.email == 'brcwood48@gmail.com'
                assert bruce_session.court_number == 'Court 3'
                assert bruce_session.assigned_time_slot == '1400'
    
    @pytest.mark.asyncio
    async def test_initialize_sessions_no_assignments_for_day(self, mock_sheets_manager):
        """Test initializing sessions when no assignments exist for the target day."""
        
        manager = MultiSessionManager(mock_sheets_manager)
        
        result = await manager.initialize_sessions_with_assignments('Monday', headless=True)
        
        assert result is False
        assert len(manager.sessions) == 0
    
    @pytest.mark.asyncio
    async def test_book_assigned_slots(self, mock_sheets_manager):
        """Test booking pre-assigned slots."""
        
        # Create a mock session with assigned slot
        mock_session = Mock(spec=BookingSession)
        mock_session.account_name = 'Mother'
        mock_session.assigned_time_slot = '1400'
        mock_session.book_slots_for_day = AsyncMock(return_value=True)
        mock_session.successful_bookings = [('court_url', '12/01/2024', '1400')]
        mock_session.failed_bookings = []
        
        manager = MultiSessionManager(mock_sheets_manager)
        manager.sessions = [mock_session]
        
        result = await manager.book_assigned_slots('12/01/2024')
        
        assert result is True
        mock_session.book_slots_for_day.assert_called_once_with('12/01/2024', ['1400'])
        assert len(manager.all_successful_bookings) == 1
        assert len(manager.all_failed_bookings) == 0


class TestBookingOrchestrator:
    """Test the updated BookingOrchestrator functionality."""
    
    @pytest.fixture
    def mock_orchestrator_components(self):
        """Create mocked components for the orchestrator."""
        with patch('booking_orchestrator.GSHEET_MAIN_ID', 'test_sheet_id'), \
             patch('booking_orchestrator.GOOGLE_SERVICE_ACCOUNT_JSON', '{"test": "creds"}'), \
             patch('booking_orchestrator.SHOW_BROWSER', False):
            
            mock_sheets = Mock(spec=SheetsManager)
            mock_multi_session = Mock(spec=MultiSessionManager)
            
            with patch('booking_orchestrator.SheetsManager', return_value=mock_sheets), \
                 patch('booking_orchestrator.MultiSessionManager', return_value=mock_multi_session):
                
                orchestrator = BookingOrchestrator()
                orchestrator.sheets_manager = mock_sheets
                orchestrator.multi_session_manager = mock_multi_session
                
                return orchestrator, mock_sheets, mock_multi_session
    
    @pytest.mark.asyncio
    async def test_initialize_simplified_system(self, mock_orchestrator_components):
        """Test initializing the simplified booking system."""
        orchestrator, mock_sheets, mock_multi_session = mock_orchestrator_components
        
        result = await orchestrator.initialize()
        
        assert result is True
        assert orchestrator.sheets_manager is not None
        assert orchestrator.multi_session_manager is not None
    
    @pytest.mark.asyncio
    async def test_execute_booking_process_simplified(self, mock_orchestrator_components):
        """Test the complete simplified booking process."""
        orchestrator, mock_sheets, mock_multi_session = mock_orchestrator_components
        
        # Mock the target date calculation
        orchestrator.target_date = datetime.now().date() + timedelta(days=35)
        orchestrator.target_day_name = orchestrator.target_date.strftime('%A')
        
        # Mock all the async methods
        mock_multi_session.initialize_sessions_with_assignments = AsyncMock(return_value=True)
        mock_multi_session.login_all_sessions = AsyncMock(return_value=True)
        mock_multi_session.book_assigned_slots = AsyncMock(return_value=True)
        mock_multi_session.checkout_all_sessions = AsyncMock(return_value=True)
        mock_multi_session.logout_all_sessions = AsyncMock(return_value=True)
        mock_multi_session.cleanup_all_sessions = AsyncMock(return_value=True)
        mock_multi_session.get_booking_summary = Mock(return_value={
            'total_sessions': 2,
            'successful_bookings': 2,
            'failed_bookings': 0,
            'successful_details': [],
            'failed_details': []
        })
        mock_multi_session.get_session_details = Mock(return_value=[])
        
        # Mock the email functionality
        with patch.object(orchestrator, 'send_email_notification', new_callable=AsyncMock):
            result = await orchestrator.execute_booking_process()
        
        assert result is True
        
        # Verify the correct sequence of calls
        mock_multi_session.initialize_sessions_with_assignments.assert_called_once()
        mock_multi_session.login_all_sessions.assert_called_once()
        mock_multi_session.book_assigned_slots.assert_called_once()
        mock_multi_session.checkout_all_sessions.assert_called_once()
        mock_multi_session.logout_all_sessions.assert_called_once()
        mock_multi_session.cleanup_all_sessions.assert_called_once()


class TestBookingSession:
    """Test BookingSession with assigned time slots."""
    
    @pytest.fixture
    def mock_session_components(self):
        """Create mocked components for a booking session."""
        mock_sheets = Mock(spec=SheetsManager)
        return mock_sheets
    
    def test_session_creation_with_assignment(self, mock_session_components):
        """Test creating a session and assigning a time slot."""
        session = BookingSession(
            account_name='Mother',
            email='1140749429@qq.com',
            password='test_password',
            court_number='Court 1',
            court_url='https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
            sheets_manager=mock_session_components
        )
        
        # Assign a time slot (this would normally be done by MultiSessionManager)
        session.assigned_time_slot = '1400'
        
        assert session.account_name == 'Mother'
        assert session.email == '1140749429@qq.com'
        assert session.court_number == 'Court 1'
        assert session.assigned_time_slot == '1400'
        assert hasattr(session, 'assigned_time_slot')


class TestIntegration:
    """Integration tests for the complete simplified system."""
    
    @pytest.mark.asyncio
    async def test_complete_booking_flow_mock(self):
        """Test the complete booking flow with mocked components."""
        
        # Mock booking assignments data
        mock_assignments = [
            {
                'Account': 'Mother',
                'Email': '1140749429@qq.com',
                'Court Number': 'Court 1',
                'Day': 'Saturday',
                'Time': '1400',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
                'Notes': 'All year'
            },
            {
                'Account': 'Father',
                'Email': 'huay43105@gmail.com',
                'Court Number': 'Court 2',
                'Day': 'Saturday',
                'Time': '1500',
                'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/',
                'Notes': 'All year'
            }
        ]
        
        with patch.dict(os.environ, {
            'MOTHER_CAM_PASSWORD': 'mother_pass',
            'FATHER_CAM_PASSWORD': 'father_pass',
            'GSHEET_CAM_ID': 'test_sheet_id',
            'GOOGLE_SERVICE_ACCOUNT_JSON': '{"test": "creds"}'
        }):
            # Mock all external dependencies
            with patch('booking_orchestrator.SheetsManager') as mock_sheets_class, \
                 patch.object(BookingSession, 'initialize_browser', new_callable=AsyncMock) as mock_init_browser, \
                 patch.object(BookingSession, 'login', new_callable=AsyncMock) as mock_login, \
                 patch.object(BookingSession, 'book_slots_for_day', new_callable=AsyncMock) as mock_book_slots, \
                 patch.object(BookingSession, 'checkout', new_callable=AsyncMock) as mock_checkout, \
                 patch.object(BookingSession, 'logout', new_callable=AsyncMock) as mock_logout, \
                 patch.object(BookingSession, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
                
                # Setup mock returns
                mock_sheets_instance = Mock()
                mock_sheets_instance.read_booking_assignments.return_value = mock_assignments
                mock_sheets_class.return_value = mock_sheets_instance
                
                mock_init_browser.return_value = True
                mock_login.return_value = True
                mock_book_slots.return_value = True
                mock_checkout.return_value = True
                mock_logout.return_value = True
                mock_cleanup.return_value = True
                
                # Create and run orchestrator
                orchestrator = BookingOrchestrator()
                await orchestrator.initialize()
                
                # Mock target date to Saturday
                orchestrator.target_date = datetime(2024, 1, 13)  # A Saturday
                orchestrator.target_day_name = 'Saturday'
                
                # Mock email functionality
                with patch.object(orchestrator, 'send_email_notification', new_callable=AsyncMock):
                    result = await orchestrator.execute_booking_process()
                
                assert result is True
                
                # Verify sessions were created correctly
                assert len(orchestrator.multi_session_manager.sessions) == 2
                
                # Verify Mother's session
                mother_session = orchestrator.multi_session_manager.sessions[0]
                assert mother_session.account_name == 'Mother'
                assert mother_session.assigned_time_slot == '1400'
                
                # Verify Father's session
                father_session = orchestrator.multi_session_manager.sessions[1]
                assert father_session.account_name == 'Father'
                assert father_session.assigned_time_slot == '1500'


def test_booking_assignments_validation():
    """Test validation of booking assignments data structure."""
    
    # Test valid assignment
    valid_assignment = {
        'Account': 'Mother',
        'Email': '1140749429@qq.com',
        'Court Number': 'Court 1',
        'Day': 'Saturday',
        'Time': '1400',
        'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
        'Notes': 'All year'
    }
    
    required_fields = ['Account', 'Email', 'Court Number', 'Day', 'Time', 'Court URL']
    
    for field in required_fields:
        assert field in valid_assignment
        assert valid_assignment[field].strip() != ''
    
    # Test time format
    assert valid_assignment['Time'].isdigit()
    assert len(valid_assignment['Time']) == 4
    
    # Test day format
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    assert valid_assignment['Day'] in valid_days


if __name__ == "__main__":
    # Run the tests
    print("🧪 Running Simplified Booking System Tests")
    print("=" * 50)
    
    # Run pytest programmatically
    import subprocess
    result = subprocess.run([
        sys.executable, '-m', 'pytest', __file__, '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    exit_code = result.returncode
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    exit(exit_code)
