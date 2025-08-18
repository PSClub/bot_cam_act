#!/usr/bin/env python3
"""
Test script to verify email screenshot attachments functionality.
"""

import os
import sys
import tempfile
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_manager import EmailManager

def create_test_screenshot(filename, text="Test Screenshot"):
    """Create a simple test screenshot for testing attachments."""
    # Create a simple test image
    img = Image.new('RGB', (400, 200), color='lightblue')
    
    # Save the image
    img.save(filename)
    return filename

def test_screenshot_attachment():
    """Test that screenshots can be attached to emails."""
    print("🧪 Testing Email Screenshot Attachment Functionality")
    print("=" * 60)
    
    try:
        # Create temporary test screenshots
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot1 = os.path.join(temp_dir, "test_screenshot_1.png")
            screenshot2 = os.path.join(temp_dir, "test_screenshot_2.png")
            
            # Create test images
            create_test_screenshot(screenshot1, "Test Screenshot 1")
            create_test_screenshot(screenshot2, "Test Screenshot 2")
            
            print(f"✅ Created test screenshots:")
            print(f"   - {screenshot1}")
            print(f"   - {screenshot2}")
            
            # Test EmailManager attachment functionality
            email_manager = EmailManager("test@example.com", "test_password")
            
            # Test the _attach_screenshots method directly
            from email.mime.multipart import MIMEMultipart
            msg = MIMEMultipart()
            
            screenshot_paths = [screenshot1, screenshot2]
            attached_count = email_manager._attach_screenshots(msg, screenshot_paths)
            
            print(f"✅ Attachment test completed:")
            print(f"   - Screenshots to attach: {len(screenshot_paths)}")
            print(f"   - Successfully attached: {attached_count}")
            print(f"   - Email parts: {len(msg.get_payload())}")  # Should be attachments + text body
            
            # Verify the attachments are in the email
            attachments_found = []
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments_found.append(filename)
            
            print(f"✅ Attachments found in email: {len(attachments_found)}")
            for filename in attachments_found:
                print(f"   - {filename}")
            
            if attached_count == len(screenshot_paths):
                print("🎉 Screenshot attachment test PASSED!")
                return True
            else:
                print("❌ Screenshot attachment test FAILED!")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_missing_files():
    """Test behavior when screenshot files don't exist."""
    print("\n🧪 Testing Missing Screenshot Files Handling")
    print("=" * 60)
    
    try:
        email_manager = EmailManager("test@example.com", "test_password")
        
        # Test with non-existent files
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        
        missing_paths = ["/nonexistent/path1.png", "/nonexistent/path2.png"]
        attached_count = email_manager._attach_screenshots(msg, missing_paths)
        
        print(f"✅ Missing files test completed:")
        print(f"   - Screenshots to attach: {len(missing_paths)}")
        print(f"   - Successfully attached: {attached_count}")
        
        if attached_count == 0:
            print("🎉 Missing files handling test PASSED!")
            return True
        else:
            print("❌ Missing files handling test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Email Screenshot Attachment Tests")
    print("=" * 60)
    
    # Test 1: Screenshot attachment functionality
    test1_passed = test_screenshot_attachment()
    
    # Test 2: Missing files handling
    test2_passed = test_missing_files()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   ✅ Screenshot Attachment: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"   ✅ Missing Files Handling: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("🎉 All tests PASSED! Screenshot email attachments should work correctly.")
    else:
        print("❌ Some tests FAILED! Please review the implementation.")
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)
