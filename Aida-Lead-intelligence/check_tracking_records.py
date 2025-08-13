#!/usr/bin/env python3
"""
Check Tracking Records Script

This script checks what tracking records exist in the database.
"""

from models.database import Database
from services.email_tracker import EmailTracker

def check_tracking_records():
    """Check what tracking records exist"""
    print("🔍 Checking Tracking Records")
    print("=" * 40)
    
    try:
        # Initialize database and tracker
        db = Database()
        tracker = EmailTracker(db)
        
        # Get all tracking records
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, tracking_id, email_address, subject, created_at, 
                   (SELECT COUNT(*) FROM email_tracking_events WHERE tracking_id = email_tracking.tracking_id) as event_count
            FROM email_tracking 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        if records:
            print(f"✅ Found {len(records)} tracking records:")
            print()
            
            for record in records:
                record_id, tracking_id, email_address, subject, created_at, event_count = record
                print(f"📧 Record ID: {record_id}")
                print(f"   Tracking ID: {tracking_id}")
                print(f"   Email: {email_address}")
                print(f"   Subject: {subject}")
                print(f"   Created: {created_at}")
                print(f"   Events: {event_count}")
                print()
        else:
            print("❌ No tracking records found")
            print("   Send a test email first to create tracking records")
        
        # Test a tracking ID
        if records:
            test_tracking_id = records[0][1]  # Use the first tracking ID
            print(f"🧪 Testing tracking ID: {test_tracking_id}")
            
            # Test the tracking endpoint
            import requests
            try:
                response = requests.get(f"http://localhost:5000/api/email/track/open/{test_tracking_id}")
                print(f"   Open tracking test: {response.status_code}")
                if response.status_code == 200:
                    print("   ✅ Open tracking works!")
                else:
                    print(f"   ❌ Open tracking failed: {response.text}")
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        
    except Exception as e:
        print(f"❌ Error checking tracking records: {e}")

def check_email_tracking_events():
    """Check email tracking events"""
    print("\n🔍 Checking Email Tracking Events")
    print("=" * 40)
    
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tracking_id, event_type, created_at, ip_address, user_agent
            FROM email_tracking_events 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        events = cursor.fetchall()
        conn.close()
        
        if events:
            print(f"✅ Found {len(events)} tracking events:")
            print()
            
            for event in events:
                tracking_id, event_type, created_at, ip_address, user_agent = event
                print(f"📊 Event: {event_type}")
                print(f"   Tracking ID: {tracking_id}")
                print(f"   Created: {created_at}")
                print(f"   IP: {ip_address}")
                print(f"   User-Agent: {user_agent[:50]}...")
                print()
        else:
            print("❌ No tracking events found")
            print("   This means no emails have been opened/clicked yet")
        
    except Exception as e:
        print(f"❌ Error checking events: {e}")

def main():
    print("📧 Tracking Records Checker")
    print("=" * 40)
    print()
    
    check_tracking_records()
    check_email_tracking_events()
    
    print("📋 Summary")
    print("=" * 20)
    print("1. Send a test email to create tracking records")
    print("2. Use the real tracking ID to test endpoints")
    print("3. Check Flask logs for tracking events")
    print("4. Verify ngrok is forwarding requests correctly")

if __name__ == "__main__":
    main() 