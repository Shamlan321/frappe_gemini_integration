#!/usr/bin/env python3
"""
Ngrok Setup Script for Email Tracking Testing

This script helps you set up ngrok to expose your local Flask app
to the internet so email tracking can work during development.

Usage:
1. Install ngrok: https://ngrok.com/download
2. Run this script: python setup_ngrok.py
3. Update your BASE_URL environment variable with the ngrok URL
"""

import subprocess
import requests
import time
import os
import sys

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_ngrok_url():
    """Get the public URL from ngrok"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
        return None
    except:
        return None

def main():
    print("🚀 Ngrok Setup for Email Tracking Testing")
    print("=" * 50)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("❌ Ngrok is not installed!")
        print("\n📥 Please install ngrok:")
        print("1. Go to https://ngrok.com/download")
        print("2. Download and install ngrok")
        print("3. Run this script again")
        return
    
    print("✅ Ngrok is installed")
    
    # Check if Flask app is running
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running on localhost:5000")
        else:
            print("⚠️ Flask app might not be running properly")
    except:
        print("❌ Flask app is not running on localhost:5000")
        print("Please start your Flask app first:")
        print("python app.py")
        return
    
    # Start ngrok
    print("\n🌐 Starting ngrok tunnel...")
    try:
        # Start ngrok in background
        ngrok_process = subprocess.Popen(['ngrok', 'http', '5000'])
        
        # Wait for ngrok to start
        print("⏳ Waiting for ngrok to start...")
        time.sleep(3)
        
        # Get the public URL
        ngrok_url = get_ngrok_url()
        
        if ngrok_url:
            print(f"✅ Ngrok tunnel established!")
            print(f"🌍 Public URL: {ngrok_url}")
            print(f"📧 Tracking URL: {ngrok_url}/api/email/track/open/")
            
            print("\n📝 Next Steps:")
            print("1. Set your BASE_URL environment variable:")
            print(f"   export BASE_URL={ngrok_url}")
            print("   (or add it to your .env file)")
            print("\n2. Restart your Flask app")
            print("3. Send a test email")
            print("4. Open the email in Gmail - tracking should now work!")
            
            print(f"\n🔗 Your tracking endpoints will be:")
            print(f"   Open tracking: {ngrok_url}/api/email/track/open/{{tracking_id}}")
            print(f"   Click tracking: {ngrok_url}/api/email/track/click/{{tracking_id}}")
            print(f"   Unsubscribe: {ngrok_url}/api/email/track/unsubscribe/{{tracking_id}}")
            
            print(f"\n⚠️ Keep this terminal open to maintain the tunnel")
            print(f"Press Ctrl+C to stop ngrok")
            
            # Keep the script running
            try:
                ngrok_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping ngrok...")
                ngrok_process.terminate()
                ngrok_process.wait()
                print("✅ Ngrok stopped")
                
        else:
            print("❌ Failed to get ngrok URL")
            ngrok_process.terminate()
            
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        print("\n💡 Make sure ngrok is properly installed and in your PATH")

if __name__ == "__main__":
    main() 