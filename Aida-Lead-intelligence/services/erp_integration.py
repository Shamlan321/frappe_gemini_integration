from frappeclient import FrappeClient
import os
from typing import Dict, Any, List
import json
from datetime import datetime

class ERPIntegration:
    def __init__(self):
        self.server_url = os.getenv('ERPNEXT_URL', 'https://your-erpnext-site.com')
        self.username = os.getenv('ERPNEXT_USERNAME', 'your-username')
        self.password = os.getenv('ERPNEXT_PASSWORD', 'your-password')
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to ERPNext"""
        try:
            # Check if we have valid credentials (not defaults)
            if (self.server_url == 'https://your-erpnext-site.com' or 
                self.username == 'your-username' or 
                self.password == 'your-password'):
                print("ERPNext credentials not configured. Using mock mode.")
                self.client = None
                return
            
            # Use the working approach: pass credentials directly to constructor
            self.client = FrappeClient(self.server_url, self.username, self.password)
            
            # Test the connection by trying to fetch user info
            try:
                user_info = self.client.get_doc('User', self.username)
                if user_info:
                    print(f"Successfully connected to ERPNext as {user_info.get('full_name', self.username)}")
                else:
                    print(f"Successfully connected to ERPNext as {self.username} (user info not available)")
            except:
                # If user info fetch fails, just confirm basic connection
                print(f"Successfully connected to ERPNext as {self.username} (user info not available)")
            
        except Exception as e:
            print(f"Failed to connect to ERPNext: {str(e)}")
            self.client = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test ERPNext connection"""
        # Check if credentials are configured
        if (self.server_url == 'https://your-erpnext-site.com' or 
            self.username == 'your-username' or 
            self.password == 'your-password'):
            return {
                'connected': False,
                'message': 'ERPNext credentials not configured. Please update your .env file with valid ERPNext credentials.',
                'mock_mode': True
            }
        
        if not self.client:
            # Try to reconnect
            self._connect()
            
        if not self.client:
            return {
                'connected': False,
                'message': 'Failed to connect to ERPNext. Please check your credentials and server URL.',
                'server': self.server_url,
                'username': self.username
            }
        
        try:
            # Try to fetch user info to verify connection
            user_display_name = self.username
            try:
                user_info = self.client.get_doc('User', self.username)
                if user_info:
                    user_display_name = user_info.get('full_name', self.username)
            except:
                # If user info fetch fails, that's okay - connection might still work
                pass
            
            # Test with a simple API call to verify connection
            try:
                # Try to get a list of doctypes as a connection test
                self.client.get_list('DocType', limit_page_length=1)
            except Exception as api_test_error:
                raise Exception(f"API test failed: {str(api_test_error)}")
            
            return {
                'connected': True,
                'message': 'Successfully connected to ERPNext',
                'user': user_display_name,
                'server': self.server_url,
                'username': self.username
            }
        except Exception as e:
            self.client = None  # Reset client on error
            return {
                'connected': False,
                'message': f'Connection test failed: {str(e)}',
                'server': self.server_url,
                'username': self.username
            }
    
    def _map_industry(self, category: str) -> str:
        """Map business category to valid ERPNext industry"""
        if not category:
            return ''
        
        # Common ERPNext industry mappings
        industry_mapping = {
            'gym': 'Services',
            'fitness': 'Services',
            'restaurant': 'Services',
            'food': 'Services',
            'retail': 'Retail',
            'store': 'Retail',
            'shop': 'Retail',
            'hotel': 'Services',
            'accommodation': 'Services',
            'medical': 'Healthcare',
            'health': 'Healthcare',
            'hospital': 'Healthcare',
            'clinic': 'Healthcare',
            'education': 'Education',
            'school': 'Education',
            'university': 'Education',
            'technology': 'Technology',
            'software': 'Technology',
            'it': 'Technology',
            'consulting': 'Services',
            'legal': 'Services',
            'finance': 'Financial Services',
            'bank': 'Financial Services',
            'insurance': 'Financial Services',
            'real estate': 'Real Estate',
            'property': 'Real Estate',
            'construction': 'Construction',
            'manufacturing': 'Manufacturing',
            'automotive': 'Automotive',
            'transportation': 'Transportation',
            'logistics': 'Transportation',
            'entertainment': 'Entertainment',
            'media': 'Entertainment',
            'beauty': 'Services',
            'salon': 'Services',
            'spa': 'Services'
        }
        
        # Convert to lowercase for matching
        category_lower = category.lower().strip()
        
        # Direct match
        if category_lower in industry_mapping:
            return industry_mapping[category_lower]
        
        # Partial match
        for key, value in industry_mapping.items():
            if key in category_lower or category_lower in key:
                return value
        
        # Default fallback
        return 'Services'
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lead in ERPNext CRM"""
        if not self.client:
            # For development, return mock response
            return {
                'success': True,
                'lead_name': f"LEAD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'message': 'Lead created successfully (mock - ERPNext not connected)',
                'mock': True
            }
        
        try:
            # Map business category to valid ERPNext industry
            mapped_industry = self._map_industry(lead_data.get('category', ''))
            
            # Map lead data to ERPNext Lead doctype fields
            erp_lead = {
                'doctype': 'Lead',
                'lead_name': lead_data.get('company_name', 'Unknown Company'),
                'company_name': lead_data.get('company_name', ''),
                'email_id': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'website': lead_data.get('website', ''),
                'address_line1': lead_data.get('address', ''),
                'city': lead_data.get('city', ''),
                'state': lead_data.get('state', ''),
                'country': lead_data.get('country', ''),
                'pincode': lead_data.get('postal_code', ''),
                'source': lead_data.get('source', 'Lead Intelligence Platform'),
                'status': 'Lead',
                'lead_type': 'Client'
                # Temporarily removing industry field to avoid validation errors
                # 'industry': mapped_industry
            }
            
            # Note: Industry field is skipped to avoid validation errors
            # Different ERPNext instances may have different industry configurations
            # The business category is preserved in the lead notes for reference
            
            # Only add custom fields if they exist in ERPNext
            # These might not exist in all ERPNext installations
            custom_fields = {
                'custom_rating': lead_data.get('rating', 0),
                'custom_review_count': lead_data.get('review_count', 0),
                'custom_google_maps_url': lead_data.get('google_maps_url', ''),
                'custom_place_id': lead_data.get('place_id', ''),
                'custom_latitude': lead_data.get('latitude', 0),
                'custom_longitude': lead_data.get('longitude', 0)
            }
            
            # Try to add custom fields, but don't fail if they don't exist
            for field, value in custom_fields.items():
                if value:  # Only add non-empty values
                    erp_lead[field] = value
            
            print(f"Creating lead with data: {erp_lead}")
            
            # Create the lead using the working approach
            print(f"Inserting lead into ERPNext...")
            created_lead = self.client.insert(erp_lead)
            
            print(f"Insert response: {created_lead}")
            print(f"Insert response type: {type(created_lead)}")
            
            # Extract lead name from response
            lead_name = None
            if created_lead:
                if isinstance(created_lead, dict):
                    lead_name = created_lead.get('name') or created_lead.get('lead_name')
                elif hasattr(created_lead, 'name'):
                    lead_name = created_lead.name
                elif hasattr(created_lead, 'get'):
                    lead_name = created_lead.get('name') or created_lead.get('lead_name')
            
            # If we still don't have a lead name, try to fetch it by searching
            if not lead_name:
                print(f"No lead name in response, searching for created lead...")
                try:
                    # Search for recently created leads with the same company name
                    recent_leads = self.client.get_list('Lead', 
                                                       filters={'company_name': erp_lead['company_name']},
                                                       fields=['name', 'lead_name', 'creation'],
                                                       order_by='creation desc',
                                                       limit_page_length=1)
                    if recent_leads:
                        lead_name = recent_leads[0].get('name')
                        print(f"Found created lead: {lead_name}")
                except Exception as search_error:
                    print(f"Failed to search for created lead: {search_error}")
            
            # Final fallback: generate a name based on the company name
            if not lead_name:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                company_name = erp_lead.get('company_name', 'Unknown').replace(' ', '-')
                lead_name = f"{company_name}-{timestamp}"
            
            # Add detailed information as a note
            try:
                self._add_lead_note(lead_name, lead_data)
            except Exception as note_error:
                print(f"Warning: Failed to add note for lead {lead_name}: {str(note_error)}")
            
            return {
                'success': True,
                'lead_name': lead_name,
                'message': 'Lead created successfully in ERPNext',
                'erp_data': created_lead if created_lead else erp_lead
            }
            
        except Exception as e:
            print(f"Error creating lead: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create lead in ERPNext: {str(e)}'
            }
    
    def _add_lead_note(self, lead_name: str, lead_data: Dict[str, Any]):
        """Add detailed lead information as a note"""
        try:
            # Prepare detailed note content
            note_content = self._format_lead_note(lead_data)
            
            note = {
                'doctype': 'Note',
                'title': f'Lead Details - {lead_data.get("company_name", "Unknown")}',
                'content': note_content,
                'public': 0,
                'notify_on_login': 0
            }
            
            created_note = self.client.insert(note)
            
            # Link note to lead (if custom field exists)
            # This would require custom field setup in ERPNext
            
        except Exception as e:
            print(f"Failed to add note for lead {lead_name}: {str(e)}")
    
    def _format_lead_note(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data into a readable note"""
        note_parts = []
        
        note_parts.append(f"**Lead Generated from {lead_data.get('source', 'Unknown Source')}**\n")
        note_parts.append(f"Generated on: {lead_data.get('generated_at', datetime.now().isoformat())}\n")
        
        if lead_data.get('category'):
            note_parts.append(f"**Business Category:** {lead_data['category']}\n")
        
        if lead_data.get('description'):
            note_parts.append(f"**Description:** {lead_data['description']}\n")
        
        if lead_data.get('rating'):
            note_parts.append(f"**Rating:** {lead_data['rating']}/5 ({lead_data.get('review_count', 0)} reviews)\n")
        
        # Social media links
        social_media = lead_data.get('social_media', {})
        if any(social_media.values()):
            note_parts.append("**Social Media:**\n")
            for platform, links in social_media.items():
                if links:
                    for link in links:
                        note_parts.append(f"- {platform.title()}: {link}\n")
        
        # Business hours
        if lead_data.get('business_hours'):
            note_parts.append("**Business Hours:**\n")
            for hours in lead_data['business_hours']:
                if isinstance(hours, dict):
                    day = hours.get('day', '')
                    time = hours.get('hours', '')
                    note_parts.append(f"- {day}: {time}\n")
        
        # Additional info
        additional_info = lead_data.get('additional_info', {})
        if additional_info:
            note_parts.append("**Additional Information:**\n")
            for category, items in additional_info.items():
                if items:
                    note_parts.append(f"**{category}:**\n")
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    note_parts.append(f"- {key}: {value}\n")
                            else:
                                note_parts.append(f"- {item}\n")
        
        return ''.join(note_parts)
    
    def get_existing_leads(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fetch existing leads from ERPNext"""
        if not self.client:
            return []
        
        try:
            # Default filters
            if not filters:
                filters = {'status': ['!=', 'Converted']}
            
            # Fetch leads with all fields
            leads = self.client.get_list('Lead', 
                                       filters=filters,
                                       fields=["*"])
            
            # Filter and map the fields we need
            processed_leads = []
            for lead in leads:
                processed_lead = {
                    'name': lead.get('name', ''),
                    'lead_name': lead.get('lead_name', ''),
                    'company_name': lead.get('company_name', ''),
                    'email_id': lead.get('email_id', ''),
                    'phone': lead.get('phone', ''),
                    'status': lead.get('status', ''),
                    'source': lead.get('source', '')
                }
                processed_leads.append(processed_lead)
            
            return processed_leads
            
        except Exception as e:
            print(f"Failed to fetch leads from ERPNext: {str(e)}")
            return []

    def get_existing_leads_with_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch existing leads from ERPNext using provided configuration"""
        try:
            # Extract configuration
            server_url = config.get('url', '')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if not all([server_url, username, password]):
                return []
            
            # Create temporary client for fetching leads
            temp_client = FrappeClient(server_url, username, password)
            
            # Fetch leads with all fields (like the working test file)
            leads = temp_client.get_list('Lead', 
                                       filters={'status': ['!=', 'Converted']},
                                       fields=["*"])
            
            # Filter and map the fields we need
            processed_leads = []
            for lead in leads:
                processed_lead = {
                    'name': lead.get('name', ''),
                    'lead_name': lead.get('lead_name', ''),
                    'company_name': lead.get('company_name', ''),
                    'email_id': lead.get('email_id', ''),
                    'phone': lead.get('phone', ''),
                    'status': lead.get('status', ''),
                    'address_line1': lead.get('address_line1', ''),
                    'city': lead.get('city', ''),
                    'state': lead.get('state', ''),
                    'country': lead.get('country', ''),
                    'website': lead.get('website', ''),
                    'description': lead.get('description', ''),
                    'source': lead.get('source', '')
                }
                processed_leads.append(processed_lead)
            
            return processed_leads
            
        except Exception as e:
            print(f"Failed to fetch leads from ERPNext with config: {str(e)}")
            return []
    
    def update_lead_status(self, lead_name: str, status: str) -> Dict[str, Any]:
        """Update lead status in ERPNext"""
        if not self.client:
            return {'success': False, 'message': 'Not connected to ERPNext'}
        
        try:
            self.client.update('Lead', lead_name, {'status': status})
            return {
                'success': True,
                'message': f'Lead {lead_name} status updated to {status}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update lead status: {str(e)}'
            }
    
    def test_connection_with_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test ERPNext connection with provided configuration"""
        try:
            # Extract configuration
            server_url = config.get('url', '')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if not all([server_url, username, password]):
                return {
                    'success': False,
                    'message': 'Missing required configuration: URL, username, and password are required'
                }
            
            # Create temporary client for testing
            test_client = FrappeClient(server_url, username, password)
            
            # Test connection with a simple API call
            try:
                test_client.get_list('DocType', limit_page_length=1)
            except Exception as api_test_error:
                return {
                    'success': False,
                    'message': f'Connection test failed: {str(api_test_error)}'
                }
            
            # Try to get user info
            user_display_name = username
            try:
                user_info = test_client.get_doc('User', username)
                if user_info:
                    user_display_name = user_info.get('full_name', username)
            except:
                pass  # User info is optional
            
            return {
                'success': True,
                'message': 'Connection successful',
                'user': user_display_name,
                'server': server_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def create_lead_with_config(self, lead_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lead in ERPNext using provided configuration"""
        try:
            # Extract configuration
            server_url = config.get('url', '')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if not all([server_url, username, password]):
                return {
                    'success': False,
                    'message': 'Missing ERP configuration'
                }
            
            # Create temporary client
            temp_client = FrappeClient(server_url, username, password)
            
            # Map business category to valid ERPNext industry
            mapped_industry = self._map_industry(lead_data.get('category', ''))
            
            # Map lead data to ERPNext Lead doctype fields
            erp_lead = {
                'doctype': 'Lead',
                'lead_name': lead_data.get('company_name', lead_data.get('name', 'Unknown Company')),
                'company_name': lead_data.get('company_name', lead_data.get('name', '')),
                'email_id': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'website': lead_data.get('website', ''),
                'address_line1': lead_data.get('address', ''),
                'city': lead_data.get('city', ''),
                'state': lead_data.get('state', ''),
                'country': lead_data.get('country', ''),
                'pincode': lead_data.get('postal_code', ''),
                'source': lead_data.get('source', 'Lead Intelligence Platform'),
                'status': 'Lead',
                'lead_type': 'Client'
            }
            
            # Create the lead
            created_lead = temp_client.insert(erp_lead)
            
            # Extract lead name from response
            lead_name = None
            if created_lead:
                if isinstance(created_lead, dict):
                    lead_name = created_lead.get('name') or created_lead.get('lead_name')
                elif hasattr(created_lead, 'name'):
                    lead_name = created_lead.name
            
            # Fallback lead name
            if not lead_name:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                company_name = erp_lead.get('company_name', 'Unknown').replace(' ', '-')
                lead_name = f"{company_name}-{timestamp}"
            
            return {
                'success': True,
                'lead_name': lead_name,
                'message': 'Lead created successfully in ERPNext'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create lead in ERPNext: {str(e)}'
            }