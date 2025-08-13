import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailSender:
    def __init__(self):
        # Email configuration - you can set these in .env file or modify directly
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', 'your-app-password')
        self.sender_name = os.getenv('SENDER_NAME', 'Aida Lead Intelligence')
        
        # Test recipient - you can modify this
        self.test_recipient = os.getenv('TEST_RECIPIENT', 'test@example.com')
        
    def send_test_email(self, to_email=None, subject=None, content=None):
        """
        Send a test email to verify SMTP configuration
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            content (str): Email content (HTML)
        """
        
        # Use default values if not provided
        to_email = to_email or self.test_recipient
        subject = subject or f"Test Email from Aida Lead Intelligence - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        content = content or self.get_default_test_content()
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">🎯 Aida Lead Intelligence</h2>
                    <p>This is a test email to verify SMTP configuration.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3>Email Details:</h3>
                        <ul>
                            <li><strong>From:</strong> {self.sender_email}</li>
                            <li><strong>To:</strong> {to_email}</li>
                            <li><strong>Subject:</strong> {subject}</li>
                            <li><strong>Sent:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3>SMTP Configuration:</h3>
                        <ul>
                            <li><strong>SMTP Server:</strong> {self.smtp_server}</li>
                            <li><strong>SMTP Port:</strong> {self.smtp_port}</li>
                            <li><strong>Sender Email:</strong> {self.sender_email}</li>
                        </ul>
                    </div>
                    
                    <p style="color: #6c757d; font-size: 14px;">
                        If you received this email, the SMTP configuration is working correctly!
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="color: #6c757d; font-size: 12px; text-align: center;">
                        This is an automated test email from Aida Lead Intelligence Platform
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SMTP connection
            print(f"Connecting to {self.smtp_server}:{self.smtp_port}...")
            
            # Try TLS first, fallback to SSL if needed
            try:
                # Try TLS
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                print("✓ TLS connection established")
            except Exception as e:
                print(f"TLS failed: {e}")
                # Try SSL
                try:
                    server = smtplib.SMTP_SSL(self.smtp_server, 465)
                    print("✓ SSL connection established")
                except Exception as e2:
                    print(f"SSL failed: {e2}")
                    raise Exception("Failed to establish secure connection")
            
            # Login
            print(f"Logging in with {self.sender_email}...")
            server.login(self.sender_email, self.sender_password)
            print("✓ Login successful")
            
            # Send email
            print(f"Sending email to {to_email}...")
            server.sendmail(self.sender_email, to_email, message.as_string())
            print("✓ Email sent successfully!")
            
            # Close connection
            server.quit()
            print("✓ SMTP connection closed")
            
            return {
                'success': True,
                'message': f'Email sent successfully to {to_email}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def get_default_test_content(self):
        """Get default test email content"""
        return """
        <h2>Test Email from Aida Lead Intelligence</h2>
        <p>This is a test email to verify that the SMTP configuration is working correctly.</p>
        <p>If you received this email, the email sending functionality is ready to be integrated into the platform.</p>
        """
    
    def test_smtp_connection(self):
        """Test SMTP connection without sending email"""
        try:
            print(f"Testing connection to {self.smtp_server}:{self.smtp_port}...")
            
            # Try TLS
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                print("✓ TLS connection successful")
            except Exception as e:
                print(f"TLS failed: {e}")
                # Try SSL
                server = smtplib.SMTP_SSL(self.smtp_server, 465)
                print("✓ SSL connection successful")
            
            # Test login
            print(f"Testing login with {self.sender_email}...")
            server.login(self.sender_email, self.sender_password)
            print("✓ Login successful")
            
            # Close connection
            server.quit()
            print("✓ Connection test completed successfully")
            
            return {
                'success': True,
                'message': 'SMTP connection test successful'
            }
            
        except Exception as e:
            error_msg = f"SMTP connection test failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }

def main():
    """Main function to test email sending"""
    print("=" * 60)
    print("🎯 Aida Lead Intelligence - Email Sender Test")
    print("=" * 60)
    
    # Initialize email sender
    email_sender = EmailSender()
    
    # Display current configuration
    print("\n📧 Current Email Configuration:")
    print(f"SMTP Server: {email_sender.smtp_server}")
    print(f"SMTP Port: {email_sender.smtp_port}")
    print(f"Sender Email: {email_sender.sender_email}")
    print(f"Test Recipient: {email_sender.test_recipient}")
    print()
    
    # Test 1: Connection test
    print("🔍 Testing SMTP Connection...")
    connection_result = email_sender.test_smtp_connection()
    
    if not connection_result['success']:
        print("\n❌ Connection test failed. Please check your SMTP configuration.")
        print("Common issues:")
        print("- Incorrect SMTP server or port")
        print("- Wrong email or password")
        print("- 2FA enabled (use app password)")
        print("- Less secure app access disabled")
        return
    
    print("\n✅ Connection test successful!")
    
    # Test 2: Send test email
    print("\n📤 Sending test email...")
    email_result = email_sender.send_test_email()
    
    if email_result['success']:
        print("\n🎉 Email test completed successfully!")
        print("The email sending functionality is ready for integration.")
    else:
        print("\n❌ Email test failed.")
        print("Please check the error message above and verify your configuration.")

if __name__ == "__main__":
    main() 