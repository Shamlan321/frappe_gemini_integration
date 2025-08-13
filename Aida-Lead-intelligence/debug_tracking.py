#!/usr/bin/env python3
"""
Debug Email Tracking Script

This script helps debug email tracking issues by:
1. Checking if tracking records exist
2. Testing tracking endpoints
3. Verifying ngrok setup
4. Checking email content for tracking pixels
"""

import requests
import json
import os
from datetime import datetime

def check_environment():
    """Check environment variables"""
    print("🔍 Environment Check")
    print("=" * 30)
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    print(f"BASE_URL: {base_url}")
    
    if 'localhost' in base_url or '127.0.0.1' in base_url:
        print("⚠️  Using localhost - tracking won't work with external email clients")
    else:
        print("✅ Using external URL - tracking should work")
    
    print()

def check_flask_app():
    """Check if Flask app is running"""
    print("🔍 Flask App Check")
    print("=" * 30)
    
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        print(f"✅ Flask app is running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Flask app is not running: {e}")
        return False
    
    print()

def check_ngrok():
    """Check ngrok status"""
    print("🔍 Ngrok Check")
    print("=" * 30)
    
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    ngrok_url = tunnel['public_url']
                    print(f"✅ Ngrok tunnel active: {ngrok_url}")
                    
                    # Test ngrok endpoint
                    try:
                        test_response = requests.get(f"{ngrok_url}/api/email/track/open/test123", timeout=5)
                        print(f"✅ Ngrok endpoint test: {test_response.status_code}")
                    except Exception as e:
                        print(f"❌ Ngrok endpoint test failed: {e}")
                    
                    return ngrok_url
        else:
            print("❌ Ngrok API not responding")
    except Exception as e:
        print(f"❌ Ngrok not running: {e}")
    
    print()
    return None

def test_tracking_endpoints():
    """Test tracking endpoints"""
    print("🔍 Tracking Endpoints Test")
    print("=" * 30)
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    test_id = "debug_test_123"
    
    endpoints = [
        f"/api/email/track/open/{test_id}",
        f"/api/email/track/click/{test_id}",
        f"/api/email/track/unsubscribe/{test_id}"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint}")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            if response.status_code == 200:
                print(f"   Response length: {len(response.content)} bytes")
            else:
                print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint}")
            print(f"   Error: {e}")
        print()

def check_database_tracking():
    """Check if tracking records exist in database"""
    print("🔍 Database Tracking Check")
    print("=" * 30)
    
    try:
        # This would require database access
        # For now, we'll check via API if available
        response = requests.get('http://localhost:5000/api/email/track/email/1', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found tracking records: {len(data.get('events', []))} events")
        else:
            print(f"❌ No tracking records found (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    print()

def analyze_email_content():
    """Analyze email content for tracking pixels"""
    print("🔍 Email Content Analysis")
    print("=" * 30)
    
    # Sample tracking pixel that should be in emails
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    sample_tracking_id = "sample_123"
    
    expected_pixel = f'<img src="{base_url}/api/email/track/open/{sample_tracking_id}" width="1" height="1" style="display:none;" />'
    
    print("Expected tracking pixel format:")
    print(f"   {expected_pixel}")
    print()
    
    print("To check if tracking pixel is in your email:")
    print("1. Send a test email")
    print("2. View the email source (in Gmail: More → Show original)")
    print("3. Search for 'api/email/track/open/' in the HTML")
    print("4. The tracking pixel should be at the end of the email")
    print()

def check_email_tracker_config():
    """Check EmailTracker configuration"""
    print("🔍 EmailTracker Configuration")
    print("=" * 30)
    
    try:
        # Test the email tracker initialization
        from services.email_tracker import EmailTracker
        from models.database import Database
        
        db = Database()
        tracker = EmailTracker(db)
        
        print(f"✅ EmailTracker initialized successfully")
        print(f"   Base URL: {tracker.base_url}")
        
        # Test tracking pixel generation
        test_content = "<p>Test email</p>"
        test_tracking_id = "config_test_123"
        tracked_content = tracker._add_tracking_to_email(test_content, test_tracking_id)
        
        print(f"✅ Tracking pixel added successfully")
        print(f"   Original length: {len(test_content)}")
        print(f"   Tracked length: {len(tracked_content)}")
        
        if "api/email/track/open/" in tracked_content:
            print(f"✅ Tracking pixel found in content")
        else:
            print(f"❌ Tracking pixel not found in content")
        
    except Exception as e:
        print(f"❌ EmailTracker configuration failed: {e}")
    
    print()

def main():
    print("🐛 Email Tracking Debug Tool")
    print("=" * 40)
    print()
    
    # Run all checks
    check_environment()
    check_flask_app()
    ngrok_url = check_ngrok()
    test_tracking_endpoints()
    check_database_tracking()
    analyze_email_content()
    check_email_tracker_config()
    
    print("📋 Summary & Recommendations")
    print("=" * 40)
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    if 'localhost' in base_url or '127.0.0.1' in base_url:
        print("❌ Problem: Using localhost for tracking")
        print("   Solution: Set BASE_URL to ngrok URL")
        if ngrok_url:
            print(f"   Command: export BASE_URL={ngrok_url}")
        else:
            print("   Command: ngrok http 5000")
            print("   Then: export BASE_URL=<ngrok-url>")
    else:
        print("✅ Using external URL for tracking")
    
    print()
    print("🔧 Next Steps:")
    print("1. Set BASE_URL to ngrok URL")
    print("2. Restart Flask app")
    print("3. Send test email")
    print("4. Check email source for tracking pixel")
    print("5. Open email in Gmail")
    print("6. Check tracking dashboard")

if __name__ == "__main__":
    main() 