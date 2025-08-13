#!/usr/bin/env python3
"""
Simple Ngrok Setup Script

This script helps you set up ngrok and test email tracking.
"""

import subprocess
import requests
import time
import os

def start_ngrok():
    """Start ngrok and get the URL"""
    print("🚀 Starting ngrok...")
    
    try:
        # Start ngrok in background
        process = subprocess.Popen(['ngrok', 'http', '5000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for ngrok to start
        print("⏳ Waiting for ngrok to start...")
        time.sleep(3)
        
        # Get the URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                for tunnel in tunnels:
                    if tunnel['proto'] == 'https':
                        ngrok_url = tunnel['public_url']
                        print(f"✅ Ngrok started: {ngrok_url}")
                        return ngrok_url
        except Exception as e:
            print(f"❌ Error getting ngrok URL: {e}")
        
        print("❌ Failed to get ngrok URL")
        return None
        
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None

def test_tracking_with_ngrok(ngrok_url):
    """Test tracking with ngrok URL"""
    print(f"\n🧪 Testing tracking with ngrok: {ngrok_url}")
    
    # Test tracking ID from your database
    tracking_id = "c7291b14-f64c-4be7-ae0c-be940e26776c"
    
    try:
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get(f"{ngrok_url}/health", timeout=10)
        print(f"Health: {response.status_code}")
        
        # Test tracking endpoint
        print("Testing tracking endpoint...")
        response = requests.get(f"{ngrok_url}/api/email/track/open/{tracking_id}", timeout=10)
        print(f"Tracking: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Tracking works through ngrok!")
            return True
        else:
            print(f"❌ Tracking failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ngrok: {e}")
        return False

def main():
    print("📧 Ngrok Setup for Email Tracking")
    print("=" * 40)
    
    # Check if Flask is running
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
        else:
            print("❌ Flask app not responding")
            return
    except Exception as e:
        print(f"❌ Flask app not running: {e}")
        return
    
    # Start ngrok
    ngrok_url = start_ngrok()
    if not ngrok_url:
        print("❌ Failed to start ngrok")
        return
    
    # Test tracking
    success = test_tracking_with_ngrok(ngrok_url)
    
    if success:
        print(f"\n🎉 Success! Email tracking is working!")
        print(f"📝 Set your BASE_URL:")
        print(f"   $env:BASE_URL=\"{ngrok_url}\"")
        print(f"\n📧 Now send a test email and open it in Gmail!")
    else:
        print(f"\n❌ Tracking not working through ngrok")
        print(f"💡 Check ngrok logs for issues")

if __name__ == "__main__":
    main() 