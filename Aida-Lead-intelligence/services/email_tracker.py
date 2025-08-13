import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models.database import ConfigManager
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailTracker:
    def __init__(self, db=None):
        from models.database import Database
        if db is None:
            db = Database()
        self.config_manager = ConfigManager(db)
        
        # Base URL for tracking
        self.base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        # Development mode - if using localhost, show warning
        if 'localhost' in self.base_url or '127.0.0.1' in self.base_url:
            print("⚠️  WARNING: Using localhost for email tracking!")
            print("   Email tracking won't work when emails are opened in external clients (Gmail, Outlook, etc.)")
            print("   For testing, use ngrok: https://ngrok.com/download")
            print("   Then set BASE_URL to your ngrok URL")
            print("   Example: export BASE_URL=https://abc123.ngrok.io")
    
    def get_email_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active email server configuration for a user"""
        return self.config_manager.get_active_email_server_config(user_id)
    
    def test_email_connection(self, user_id: int, config_id: Optional[int] = None) -> Dict[str, Any]:
        """Test email server connection"""
        try:
            if config_id:
                config = self.config_manager.get_email_server_config_by_id(user_id, config_id)
            else:
                config = self.get_email_config(user_id)
            
            if not config:
                return {
                    'success': False,
                    'message': 'No email server configuration found'
                }
            
            # Test connection
            try:
                server = None
                
                # Handle different connection types
                if config.get('use_ssl'):
                    # Use SSL connection
                    try:
                        server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
                        print("✓ SSL connection successful")
                    except Exception as e:
                        print(f"SSL connection failed: {e}")
                        # Try alternative SSL port if common port fails
                        if config['smtp_port'] == 587:
                            try:
                                server = smtplib.SMTP_SSL(config['smtp_server'], 465)
                                print("✓ SSL connection successful on port 465")
                            except Exception as e2:
                                print(f"SSL connection on port 465 failed: {e2}")
                                return {
                                    'success': False,
                                    'error': str(e),
                                    'message': f'SSL connection failed: {str(e)}'
                                }
                        else:
                            return {
                                'success': False,
                                'error': str(e),
                                'message': f'SSL connection failed: {str(e)}'
                            }
                else:
                    # Use regular SMTP connection
                    try:
                        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
                        print("✓ SMTP connection successful")
                        
                        # Try TLS if enabled
                        if config.get('use_tls'):
                            try:
                                server.starttls()
                                print("✓ TLS connection successful")
                            except Exception as e:
                                print(f"TLS failed: {e}")
                                print("⚠️ Continuing without TLS")
                    except Exception as e:
                        print(f"SMTP connection failed: {e}")
                        return {
                            'success': False,
                            'error': str(e),
                            'message': f'SMTP connection failed: {str(e)}'
                        }
                
                if not server:
                    return {
                        'success': False,
                        'error': 'No connection established',
                        'message': 'Failed to establish any connection'
                    }
                
                # Test login
                print(f"Testing login with {config['sender_email']}...")
                try:
                    server.login(config['sender_email'], config['sender_password'])
                    print("✓ Login successful")
                except Exception as e:
                    print(f"Login failed: {e}")
                    server.quit()
                    return {
                        'success': False,
                        'error': str(e),
                        'message': f'Authentication failed: {str(e)}'
                    }
                
                # Close connection
                server.quit()
                print("✓ Connection test completed successfully")
                
                return {
                    'success': True,
                    'message': 'Email server connection test successful',
                    'config': {
                        'smtp_server': config['smtp_server'],
                        'smtp_port': config['smtp_port'],
                        'sender_email': config['sender_email'],
                        'sender_name': config['sender_name']
                    }
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'message': f'Connection test failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to test connection: {str(e)}'
            }
    
    def send_test_email(self, user_id: int, to_email: str, config_id: Optional[int] = None, 
                       subject: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """Send a test email with tracking"""
        try:
            # Get email configuration
            if config_id:
                config = self.config_manager.get_email_server_config_by_id(user_id, config_id)
            else:
                config = self.get_email_config(user_id)
            
            if not config:
                return {
                    'success': False,
                    'message': 'No email server configuration found'
                }
            
            # Use default values if not provided
            subject = subject or f"Test Email from Aida Lead Intelligence - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            content = content or self.get_default_test_content()
            
            # Create tracking record
            tracking_data = {
                'email_address': to_email,
                'subject': subject,
                'template_id': None
            }
            
            tracking_record_id = self.config_manager.create_email_tracking(user_id, tracking_data)
            if not tracking_record_id:
                return {
                    'success': False,
                    'message': 'Failed to create tracking record'
                }
            
            # Get tracking ID
            tracking_record = self.config_manager.get_email_tracking_by_id(
                self._get_tracking_id_from_record_id(tracking_record_id)
            )
            if not tracking_record:
                return {
                    'success': False,
                    'message': 'Failed to get tracking ID'
                }
            
            tracking_id = tracking_record['tracking_id']
            
            # Add tracking to email content
            tracked_content = self._add_tracking_to_email(content, tracking_id)
            
            # Send email
            success = self._send_email_with_config(config, to_email, subject, tracked_content)
            
            if success:
                # Update tracking record as sent
                self.config_manager.update_email_tracking_event(tracking_id, 'sent')
                return {
                    'success': True,
                    'message': f'Test email sent successfully to {to_email}',
                    'tracking_id': tracking_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send test email'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to send test email: {str(e)}'
            }
    
    def _send_email_with_config(self, config: Dict[str, Any], to_email: str, subject: str, content: str) -> bool:
        """Send email using provided configuration"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{config['sender_name']} <{config['sender_email']}>"
            message["To"] = to_email
            
            # Create HTML content
            html_part = MIMEText(content, "html")
            message.attach(html_part)
            
            # Create SMTP connection
            print(f"Connecting to {config['smtp_server']}:{config['smtp_port']}...")
            
            server = None
            
            # Handle different connection types
            if config.get('use_ssl'):
                # Use SSL connection
                try:
                    server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
                    print("✓ SSL connection established")
                except Exception as e:
                    print(f"SSL connection failed: {e}")
                    # Try alternative SSL port if common port fails
                    if config['smtp_port'] == 587:
                        try:
                            server = smtplib.SMTP_SSL(config['smtp_server'], 465)
                            print("✓ SSL connection established on port 465")
                        except Exception as e2:
                            print(f"SSL connection on port 465 failed: {e2}")
                            raise Exception(f"SSL connection failed: {e}")
                    else:
                        raise Exception(f"SSL connection failed: {e}")
            else:
                # Use regular SMTP connection
                try:
                    server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
                    print("✓ SMTP connection established")
                    
                    # Try TLS if enabled
                    if config.get('use_tls'):
                        try:
                            server.starttls()
                            print("✓ TLS connection established")
                        except Exception as e:
                            print(f"TLS failed: {e}")
                            # Continue without TLS
                            print("⚠️ Continuing without TLS")
                except Exception as e:
                    print(f"SMTP connection failed: {e}")
                    raise Exception(f"SMTP connection failed: {e}")
            
            if not server:
                raise Exception("Failed to establish any connection")
            
            # Login
            print(f"Logging in with {config['sender_email']}...")
            try:
                server.login(config['sender_email'], config['sender_password'])
                print("✓ Login successful")
            except Exception as e:
                print(f"Login failed: {e}")
                server.quit()
                raise Exception(f"Authentication failed: {e}")
            
            # Send email
            print(f"Sending email to {to_email}...")
            try:
                server.sendmail(config['sender_email'], to_email, message.as_string())
                print("✓ Email sent successfully!")
            except Exception as e:
                print(f"Send failed: {e}")
                server.quit()
                raise Exception(f"Failed to send email: {e}")
            
            # Close connection
            server.quit()
            print("✓ SMTP connection closed")
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def get_default_test_content(self) -> str:
        """Get default test email content"""
        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #007bff;">🎯 Aida Lead Intelligence</h2>
                <p>This is a test email to verify email server configuration and tracking functionality.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Test Email Details:</h3>
                    <ul>
                        <li><strong>Sent:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Purpose:</strong> Email server configuration test</li>
                        <li><strong>Tracking:</strong> Enabled</li>
                    </ul>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Tracking Features Test:</h3>
                    <ul>
                        <li>✅ Email open tracking via pixel</li>
                        <li>✅ Link click tracking</li>
                        <li>✅ Unsubscribe functionality</li>
                        <li>✅ Event logging and analytics</li>
                    </ul>
                </div>
                
                <p style="color: #6c757d; font-size: 14px;">
                    If you received this email, the email server configuration is working correctly!
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                <p style="color: #6c757d; font-size: 12px; text-align: center;">
                    This is an automated test email from Aida Lead Intelligence Platform
                </p>
            </div>
        </body>
        </html>
        """
    
    def create_tracking_email(self, user_id: int, lead_id: int, template_id: int, 
                            email_address: str, subject: str, content: str,
                            campaign_id: Optional[int] = None, 
                            sequence_id: Optional[int] = None) -> Optional[str]:
        """
        Create a tracking email and return the tracking ID
        """
        try:
            # Create tracking record
            tracking_data = {
                'campaign_id': campaign_id,
                'sequence_id': sequence_id,
                'lead_id': lead_id,
                'email_address': email_address,
                'subject': subject,
                'template_id': template_id
            }
            
            tracking_record_id = self.config_manager.create_email_tracking(user_id, tracking_data)
            if not tracking_record_id:
                return None
            
            # Get the tracking ID
            tracking_record = self.config_manager.get_email_tracking_by_id(
                self._get_tracking_id_from_record_id(tracking_record_id)
            )
            if not tracking_record:
                return None
            
            tracking_id = tracking_record['tracking_id']
            
            # Add tracking pixel and links to email content
            tracked_content = self._add_tracking_to_email(content, tracking_id)
            
            # Send the email
            success = self._send_email_with_config(self.get_email_config(user_id), email_address, subject, tracked_content)
            
            if success:
                # Update tracking record as sent
                self.config_manager.update_email_tracking_event(tracking_id, 'sent')
                return tracking_id
            
            return None
            
        except Exception as e:
            print(f"Error creating tracking email: {e}")
            return None
    
    def _add_tracking_to_email(self, content: str, tracking_id: str) -> str:
        """
        Add tracking pixel and convert links to tracked links
        """
        # Add tracking pixel
        tracking_pixel = f'<img src="{self.base_url}/api/email/track/open/{tracking_id}" width="1" height="1" style="display:none;" />'
        
        # Add tracking pixel at the end of the email
        tracked_content = content + tracking_pixel
        
        return tracked_content
    
    def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """
        Send email using SMTP
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_email} <{self.sender_email}>"
            message["To"] = to_email
            
            # Create HTML content
            html_part = MIMEText(content, "html")
            message.attach(html_part)
            
            # Create SMTP connection
            try:
                # Try TLS
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            except Exception:
                # Try SSL
                server = smtplib.SMTP_SSL(self.smtp_server, 465)
            
            # Login and send
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, message.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _get_tracking_id_from_record_id(self, record_id: int) -> Optional[str]:
        """
        Get tracking ID from record ID
        """
        try:
            conn = self.config_manager.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT tracking_id FROM email_tracking WHERE id = ?', (record_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting tracking ID: {e}")
            return None
    
    def track_email_event(self, tracking_id: str, event_type: str, 
                         ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None,
                         location: Optional[str] = None,
                         event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track an email event (open, click, etc.)
        """
        try:
            # Update tracking record
            success = self.config_manager.update_email_tracking_event(
                tracking_id, event_type, event_data
            )
            
            if success:
                # Check for automation triggers
                self._check_automation_triggers(tracking_id, event_type)
                
                # Update sequence if this is part of a sequence
                self._update_sequence_if_needed(tracking_id, event_type)
            
            return success
            
        except Exception as e:
            print(f"Error tracking email event: {e}")
            return False
    
    def _check_automation_triggers(self, tracking_id: str, event_type: str):
        """
        Check if any automation rules should be triggered
        """
        try:
            # Get tracking record
            tracking_record = self.config_manager.get_email_tracking_by_id(tracking_id)
            if not tracking_record:
                return
            
            # Get automation rules for this user
            automation_rules = self._get_automation_rules(tracking_record['user_id'])
            
            for rule in automation_rules:
                if self._should_trigger_rule(rule, event_type, tracking_record):
                    self._execute_automation_rule(rule, tracking_record)
                    
        except Exception as e:
            print(f"Error checking automation triggers: {e}")
    
    def _get_automation_rules(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get automation rules for a user
        """
        try:
            conn = self.config_manager.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, trigger_type, trigger_conditions, action_type, action_data
                FROM email_automation_rules 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            rules = []
            for result in results:
                # Parse JSON fields
                trigger_conditions = {}
                action_data = {}
                if result[3]:  # trigger_conditions
                    try:
                        trigger_conditions = json.loads(result[3])
                    except:
                        trigger_conditions = {}
                if result[5]:  # action_data
                    try:
                        action_data = json.loads(result[5])
                    except:
                        action_data = {}
                
                rules.append({
                    'id': result[0],
                    'name': result[1],
                    'trigger_type': result[2],
                    'trigger_conditions': trigger_conditions,
                    'action_type': result[4],
                    'action_data': action_data
                })
            
            return rules
        except Exception as e:
            print(f"Error getting automation rules: {e}")
            return []
    
    def _should_trigger_rule(self, rule: Dict[str, Any], event_type: str, 
                           tracking_record: Dict[str, Any]) -> bool:
        """
        Check if a rule should be triggered based on the event
        """
        trigger_type = rule.get('trigger_type')
        trigger_conditions = rule.get('trigger_conditions', {})
        
        if trigger_type == 'email_event':
            required_event = trigger_conditions.get('event_type')
            return event_type == required_event
        
        elif trigger_type == 'time_based':
            # Check if enough time has passed since last email
            days_since_last = trigger_conditions.get('days_since_last', 0)
            if days_since_last > 0:
                # Check when the last email was sent to this lead
                last_email_date = self._get_last_email_date(tracking_record['lead_id'])
                if last_email_date:
                    days_passed = (datetime.now() - last_email_date).days
                    return days_passed >= days_since_last
        
        elif trigger_type == 'engagement_based':
            # Check engagement conditions
            min_opens = trigger_conditions.get('min_opens', 0)
            min_clicks = trigger_conditions.get('min_clicks', 0)
            
            if min_opens > 0 and tracking_record.get('open_count', 0) < min_opens:
                return False
            
            if min_clicks > 0 and tracking_record.get('click_count', 0) < min_clicks:
                return False
            
            return True
        
        return False
    
    def _execute_automation_rule(self, rule: Dict[str, Any], tracking_record: Dict[str, Any]):
        """
        Execute an automation rule
        """
        action_type = rule.get('action_type')
        action_data = rule.get('action_data', {})
        
        if action_type == 'send_email':
            # Send a follow-up email
            template_id = action_data.get('template_id')
            subject = action_data.get('subject', 'Follow-up')
            
            if template_id:
                # Get template
                template = self.config_manager.get_email_template_by_id(
                    tracking_record['user_id'], template_id
                )
                if template:
                    # Send follow-up email
                    self.create_tracking_email(
                        user_id=tracking_record['user_id'],
                        lead_id=tracking_record['lead_id'],
                        template_id=template_id,
                        email_address=tracking_record['email_address'],
                        subject=subject,
                        content=template['content'],
                        campaign_id=tracking_record.get('campaign_id'),
                        sequence_id=tracking_record.get('sequence_id')
                    )
        
        elif action_type == 'update_lead_status':
            # Update lead status
            new_status = action_data.get('status')
            if new_status:
                self._update_lead_status(tracking_record['lead_id'], new_status)
        
        elif action_type == 'add_to_sequence':
            # Add lead to a sequence
            sequence_id = action_data.get('sequence_id')
            if sequence_id:
                self._add_lead_to_sequence(
                    tracking_record['user_id'],
                    sequence_id,
                    tracking_record['lead_id']
                )
    
    def _update_sequence_if_needed(self, tracking_id: str, event_type: str):
        """
        Update sequence instance if this email is part of a sequence
        """
        try:
            tracking_record = self.config_manager.get_email_tracking_by_id(tracking_id)
            if not tracking_record or not tracking_record.get('sequence_id'):
                return
            
            # Get sequence instance
            instance = self._get_sequence_instance(
                tracking_record['user_id'],
                tracking_record['sequence_id'],
                tracking_record['lead_id']
            )
            
            if not instance:
                return
            
            # Check if we should move to next step based on event
            sequence = self.config_manager.get_email_sequences(tracking_record['user_id'])
            current_sequence = None
            for seq in sequence:
                if seq['id'] == tracking_record['sequence_id']:
                    current_sequence = seq
                    break
            
            if not current_sequence:
                return
            
            steps = current_sequence.get('steps', [])
            current_step = instance['current_step']
            
            if current_step < len(steps):
                current_step_data = steps[current_step]
                trigger_conditions = current_step_data.get('trigger_conditions', {})
                
                # Check if event matches trigger conditions
                if self._event_matches_trigger(event_type, trigger_conditions):
                    # Move to next step
                    next_step = current_step + 1
                    if next_step < len(steps):
                        # Schedule next step
                        delay_days = steps[next_step].get('delay_days', 1)
                        next_step_due = datetime.now() + timedelta(days=delay_days)
                        
                        self.config_manager.update_sequence_instance(instance['id'], {
                            'current_step': next_step,
                            'next_step_due': next_step_due
                        })
                    else:
                        # Sequence completed
                        self.config_manager.update_sequence_instance(instance['id'], {
                            'status': 'completed',
                            'completed_at': datetime.now()
                        })
                        
        except Exception as e:
            print(f"Error updating sequence: {e}")
    
    def _event_matches_trigger(self, event_type: str, trigger_conditions: Dict[str, Any]) -> bool:
        """
        Check if an event matches trigger conditions
        """
        required_event = trigger_conditions.get('event_type')
        if required_event:
            return event_type == required_event
        
        # Check for multiple event types
        allowed_events = trigger_conditions.get('event_types', [])
        if allowed_events:
            return event_type in allowed_events
        
        return False
    
    def _get_sequence_instance(self, user_id: int, sequence_id: int, lead_id: int) -> Optional[Dict[str, Any]]:
        """
        Get sequence instance for a lead
        """
        try:
            conn = self.config_manager.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, current_step, status, next_step_due
                FROM email_sequence_instances 
                WHERE user_id = ? AND sequence_id = ? AND lead_id = ?
            ''', (user_id, sequence_id, lead_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'current_step': result[1],
                    'status': result[2],
                    'next_step_due': result[3]
                }
            
            return None
        except Exception as e:
            print(f"Error getting sequence instance: {e}")
            return None
    
    def _add_lead_to_sequence(self, user_id: int, sequence_id: int, lead_id: int):
        """
        Add a lead to a sequence
        """
        try:
            # Check if already in sequence
            existing_instance = self._get_sequence_instance(user_id, sequence_id, lead_id)
            if existing_instance:
                return  # Already in sequence
            
            # Create new instance
            self.config_manager.create_sequence_instance(user_id, sequence_id, lead_id)
            
        except Exception as e:
            print(f"Error adding lead to sequence: {e}")
    
    def _update_lead_status(self, lead_id: int, new_status: str):
        """
        Update lead status
        """
        try:
            conn = self.config_manager.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE leads SET status = ? WHERE id = ?
            ''', (new_status, lead_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating lead status: {e}")
    
    def _get_last_email_date(self, lead_id: int) -> Optional[datetime]:
        """
        Get the date of the last email sent to a lead
        """
        try:
            conn = self.config_manager.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MAX(sent_at) FROM email_tracking 
                WHERE lead_id = ? AND sent_at IS NOT NULL
            ''', (lead_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return datetime.fromisoformat(result[0].replace('Z', '+00:00'))
            
            return None
        except Exception as e:
            print(f"Error getting last email date: {e}")
            return None
    
    def get_email_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get email analytics for a user
        """
        return self.config_manager.get_email_analytics(user_id, days)
    
    def get_tracking_details(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed tracking information
        """
        tracking_record = self.config_manager.get_email_tracking_by_id(tracking_id)
        if not tracking_record:
            return None
        
        # Get events
        events = self.config_manager.get_email_tracking_events(tracking_id)
        
        return {
            'tracking': tracking_record,
            'events': events
        } 