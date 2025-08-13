import frappe
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64

class ERPIntegration:
    def __init__(self):
        # Get configuration from Frappe settings
        self.settings = frappe.get_doc("Aida Lead Intelligence Settings")
        
        # Initialize connection parameters
        self.base_url = self.settings.get("erp_url", "")
        self.username = self.settings.get("erp_username", "")
        self.password = self.settings.get("erp_password", "")
        self.api_key = self.settings.get("erp_api_key", "")
        
        # Session for maintaining connection
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Test connection on initialization
        if self.base_url and self.username and self.password:
            try:
                self._authenticate()
            except Exception as e:
                frappe.logger().warning(f"Failed to authenticate with ERP on initialization: {str(e)}")
    
    def _authenticate(self) -> bool:
        """Authenticate with ERP system"""
        try:
            if not all([self.base_url, self.username, self.password]):
                raise Exception("Missing ERP connection parameters")
            
            # For Frappe/ERPNext, use the login API
            login_url = f"{self.base_url}/api/method/login"
            login_data = {
                "usr": self.username,
                "pwd": self.password
            }
            
            response = self.session.post(login_url, json=login_data)
            response.raise_for_status()
            
            # Check if login was successful
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Logged In':
                    frappe.logger().info("Successfully authenticated with ERP system")
                    return True
                else:
                    raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                raise Exception(f"Login request failed with status {response.status_code}")
                
        except Exception as e:
            frappe.logger().error(f"ERP authentication failed: {str(e)}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test ERP connection"""
        try:
            if self._authenticate():
                return {
                    'success': True,
                    'message': 'Successfully connected to ERP system',
                    'details': {
                        'url': self.base_url,
                        'username': self.username,
                        'status': 'Connected'
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to authenticate with ERP system'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'error': str(e)
            }
    
    def test_connection_with_config(self, config: Dict[str, str]) -> Dict[str, Any]:
        """Test ERP connection with provided configuration"""
        try:
            # Temporarily set configuration
            original_config = {
                'base_url': self.base_url,
                'username': self.username,
                'password': self.password,
                'api_key': self.api_key
            }
            
            self.base_url = config.get('url', '')
            self.username = config.get('username', '')
            self.password = config.get('password', '')
            self.api_key = config.get('api_key', '')
            
            # Test connection
            result = self.test_connection()
            
            # Restore original configuration
            self.base_url = original_config['base_url']
            self.username = original_config['username']
            self.password = original_config['password']
            self.api_key = original_config['api_key']
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'error': str(e)
            }
    
    def create_lead_in_erp(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lead in the ERP system"""
        try:
            if not self._authenticate():
                raise Exception("Failed to authenticate with ERP system")
            
            # Map lead data to ERP lead fields
            erp_lead_data = self._map_lead_to_erp(lead_data)
            
            # Create lead using ERP API
            lead_url = f"{self.base_url}/api/resource/Lead"
            response = self.session.post(lead_url, json=erp_lead_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data', {}).get('name'):
                frappe.logger().info(f"Successfully created lead in ERP: {result['data']['name']}")
                return {
                    'success': True,
                    'erp_lead_id': result['data']['name'],
                    'message': 'Lead created successfully in ERP'
                }
            else:
                raise Exception("Failed to create lead in ERP")
                
        except Exception as e:
            frappe.logger().error(f"Error creating lead in ERP: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to create lead in ERP: {str(e)}',
                'error': str(e)
            }
    
    def update_lead_in_erp(self, erp_lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a lead in the ERP system"""
        try:
            if not self._authenticate():
                raise Exception("Failed to authenticate with ERP system")
            
            # Map lead data to ERP lead fields
            erp_lead_data = self._map_lead_to_erp(lead_data)
            
            # Update lead using ERP API
            lead_url = f"{self.base_url}/api/resource/Lead/{erp_lead_id}"
            response = self.session.put(lead_url, json=erp_lead_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data', {}).get('name'):
                frappe.logger().info(f"Successfully updated lead in ERP: {result['data']['name']}")
                return {
                    'success': True,
                    'erp_lead_id': result['data']['name'],
                    'message': 'Lead updated successfully in ERP'
                }
            else:
                raise Exception("Failed to update lead in ERP")
                
        except Exception as e:
            frappe.logger().error(f"Error updating lead in ERP: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to update lead in ERP: {str(e)}',
                'error': str(e)
            }
    
    def get_lead_from_erp(self, erp_lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead from the ERP system"""
        try:
            if not self._authenticate():
                raise Exception("Failed to authenticate with ERP system")
            
            # Get lead using ERP API
            lead_url = f"{self.base_url}/api/resource/Lead/{erp_lead_id}"
            response = self.session.get(lead_url)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                return result['data']
            else:
                return None
                
        except Exception as e:
            frappe.logger().error(f"Error getting lead from ERP: {str(e)}")
            return None
    
    def search_leads_in_erp(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search leads in the ERP system"""
        try:
            if not self._authenticate():
                raise Exception("Failed to authenticate with ERP system")
            
            # Build search query
            filters = []
            if search_criteria.get('company_name'):
                filters.append(f'[["company_name", "like", "%{search_criteria["company_name"]}%"]]')
            if search_criteria.get('industry'):
                filters.append(f'[["industry", "=", "{search_criteria["industry"]}"]]')
            if search_criteria.get('city'):
                filters.append(f'[["city", "=", "{search_criteria["city"]}"]]')
            
            # Combine filters
            if filters:
                filter_string = ' and '.join(filters)
            else:
                filter_string = '[]'
            
            # Search leads using ERP API
            search_url = f"{self.base_url}/api/resource/Lead"
            params = {
                'filters': filter_string,
                'fields': '["name", "company_name", "industry", "city", "state", "country", "email", "phone", "website"]'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                return result['data']
            else:
                return []
                
        except Exception as e:
            frappe.logger().error(f"Error searching leads in ERP: {str(e)}")
            return []
    
    def _map_lead_to_erp(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map lead data to ERP lead fields"""
        erp_lead = {}
        
        # Basic company information
        if lead_data.get('company_name'):
            erp_lead['company_name'] = lead_data['company_name']
        
        if lead_data.get('industry'):
            erp_lead['industry'] = lead_data['industry']
        
        if lead_data.get('company_size'):
            erp_lead['company_size'] = lead_data['company_size']
        
        # Contact information
        if lead_data.get('email'):
            erp_lead['email_id'] = lead_data['email']
        
        if lead_data.get('phone'):
            erp_lead['phone'] = lead_data['phone']
        
        if lead_data.get('website'):
            erp_lead['website'] = lead_data['website']
        
        # Location information
        if lead_data.get('city'):
            erp_lead['city'] = lead_data['city']
        
        if lead_data.get('state'):
            erp_lead['state'] = lead_data['state']
        
        if lead_data.get('country'):
            erp_lead['country'] = lead_data['country']
        
        if lead_data.get('address'):
            erp_lead['address'] = lead_data['address']
        
        # Additional details
        if lead_data.get('title'):
            erp_lead['job_title'] = lead_data['title']
        
        if lead_data.get('first_name'):
            erp_lead['first_name'] = lead_data['first_name']
        
        if lead_data.get('last_name'):
            erp_lead['last_name'] = lead_data['last_name']
        
        if lead_data.get('source'):
            erp_lead['lead_source'] = lead_data['source']
        
        # Set default values
        erp_lead['status'] = 'Lead'
        erp_lead['doctype'] = 'Lead'
        
        return erp_lead
    
    def sync_leads_batch(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync multiple leads to ERP system"""
        results = {
            'success': [],
            'failed': [],
            'total': len(leads)
        }
        
        for lead in leads:
            try:
                result = self.create_lead_in_erp(lead)
                if result.get('success'):
                    results['success'].append({
                        'lead': lead,
                        'erp_id': result.get('erp_lead_id')
                    })
                else:
                    results['failed'].append({
                        'lead': lead,
                        'error': result.get('message', 'Unknown error')
                    })
            except Exception as e:
                results['failed'].append({
                    'lead': lead,
                    'error': str(e)
                })
        
        frappe.logger().info(f"Batch sync completed: {len(results['success'])} successful, {len(results['failed'])} failed")
        return results
    
    def get_erp_statistics(self) -> Dict[str, Any]:
        """Get ERP system statistics"""
        try:
            if not self._authenticate():
                raise Exception("Failed to authenticate with ERP system")
            
            stats = {}
            
            # Get total leads count
            leads_url = f"{self.base_url}/api/resource/Lead"
            response = self.session.get(leads_url, params={'limit_page_length': 1})
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                stats['total_leads'] = result.get('total_count', 0)
            
            # Get leads by status
            statuses = ['Lead', 'Open', 'Replied', 'Opportunity', 'Quotation', 'Lost Quotation', 'Interested', 'Converted', 'Do Not Contact']
            status_counts = {}
            
            for status in statuses:
                try:
                    status_response = self.session.get(leads_url, params={
                        'filters': f'[["status", "=", "{status}"]]',
                        'limit_page_length': 1
                    })
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status_counts[status] = status_result.get('total_count', 0)
                except:
                    status_counts[status] = 0
            
            stats['leads_by_status'] = status_counts
            
            return stats
            
        except Exception as e:
            frappe.logger().error(f"Error getting ERP statistics: {str(e)}")
            return {}