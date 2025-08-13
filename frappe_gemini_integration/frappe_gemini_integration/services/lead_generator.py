import frappe
import os
from typing import List, Dict, Any
import json
from datetime import datetime
import requests
from apify_client import ApifyClient

class LeadGenerator:
    def __init__(self):
        # Get configuration from Frappe settings
        self.settings = frappe.get_doc("Aida Lead Intelligence Settings")
        
        # Initialize Apify client
        self.apify_token = self.settings.get("apify_token") or os.getenv('APIFY_TOKEN')
        if self.apify_token:
            self.client = ApifyClient(self.apify_token)
        else:
            self.client = None
            frappe.log_error("Apify token not configured", "Lead Generator")
        
        # Google Maps Actor ID
        self.gmaps_actor_id = "WnMxbsRLNbPeYL6ge"
        
        # Apollo API configuration
        self.apollo_api_key = self.settings.get("apollo_api_key") or os.getenv('APOLLO_API_KEY')
        self.apollo_host = "apollo-io-no-cookies-required.p.rapidapi.com"
        
    def generate_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate leads based on criteria"""
        source = criteria.get('source', 'gmaps')
        
        if source == 'gmaps':
            return self._generate_gmaps_leads(criteria)
        elif source == 'apollo':
            return self._generate_apollo_leads(criteria)
        else:
            raise ValueError(f"Unsupported lead source: {source}")
    
    def _generate_gmaps_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate leads from Google Maps"""
        try:
            if not self.client:
                raise Exception("Apify client not configured")
            
            frappe.logger().info(f"Generating Google Maps leads with criteria: {criteria}")
            
            # Prepare the Actor input based on criteria
            run_input = {
                "searchStringsArray": criteria.get('search_terms', ['restaurant']),
                "locationQuery": criteria.get('location', 'New York, USA'),
                "maxCrawledPlacesPerSearch": criteria.get('max_leads', 2),
                "language": criteria.get('language', 'en'),
                "placeMinimumStars": criteria.get('min_rating', ''),
                "website": "allPlaces",
                "searchMatching": "all",
                "skipClosedPlaces": criteria.get('skip_closed', False),
            }
            
            # Add filters if specified
            if criteria.get('require_email', False):
                run_input["onlyDataWithEmails"] = True
            if criteria.get('require_phone', False):
                run_input["onlyDataWithPhones"] = True
            
            frappe.logger().info(f"Running Google Maps actor with input: {run_input}")
            
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.gmaps_actor_id).call(run_input=run_input)
            frappe.logger().info(f"Actor run completed. Dataset ID: {run['defaultDatasetId']}")
            
            # Fetch and process results
            leads = []
            item_count = 0
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                item_count += 1
                lead = self._process_gmaps_lead(item)
                leads.append(lead)
                frappe.logger().info(f"Processed lead {item_count}: {lead.get('company_name', 'Unknown')}")
            
            frappe.logger().info(f"Generated {len(leads)} leads from Google Maps")
            return leads
            
        except Exception as e:
            frappe.log_error(f"Error generating Google Maps leads: {str(e)}", "Lead Generator")
            raise
    
    def _generate_apollo_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate leads from Apollo API"""
        try:
            if not self.apollo_api_key:
                raise Exception("Apollo API key not configured")
            
            frappe.logger().info(f"Generating Apollo leads with criteria: {criteria}")
            
            url = criteria.get('url', '')
            page = criteria.get('page', 1)
            
            if not url:
                raise ValueError("Apollo URL is required")
            
            headers = {
                "X-RapidAPI-Key": self.apollo_api_key,
                "X-RapidAPI-Host": self.apollo_host
            }
            
            response = requests.get(url, headers=headers, params={"page": page})
            response.raise_for_status()
            
            data = response.json()
            leads = []
            
            # Process Apollo data based on their API structure
            if 'data' in data and 'people' in data['data']:
                for person in data['data']['people']:
                    lead = self._process_apollo_lead(person)
                    leads.append(lead)
            
            frappe.logger().info(f"Generated {len(leads)} leads from Apollo")
            return leads
            
        except Exception as e:
            frappe.log_error(f"Error generating Apollo leads: {str(e)}", "Lead Generator")
            raise
    
    def _process_gmaps_lead(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process Google Maps lead data"""
        return {
            'company_name': item.get('title', 'Unknown Company'),
            'address': item.get('address', ''),
            'city': item.get('city', ''),
            'state': item.get('state', ''),
            'country': item.get('country', ''),
            'phone': item.get('phone', ''),
            'website': item.get('website', ''),
            'email': item.get('email', ''),
            'rating': item.get('rating', 0),
            'reviews_count': item.get('reviewsCount', 0),
            'category': item.get('category', ''),
            'latitude': item.get('latitude', 0),
            'longitude': item.get('longitude', 0),
            'source': 'google_maps',
            'generated_at': datetime.now().isoformat()
        }
    
    def _process_apollo_lead(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """Process Apollo lead data"""
        return {
            'company_name': person.get('organization', {}).get('name', 'Unknown Company'),
            'first_name': person.get('first_name', ''),
            'last_name': person.get('last_name', ''),
            'email': person.get('email', ''),
            'phone': person.get('phone', ''),
            'title': person.get('title', ''),
            'industry': person.get('organization', {}).get('industry', ''),
            'company_size': person.get('organization', {}).get('employee_count', ''),
            'website': person.get('organization', {}).get('website_url', ''),
            'city': person.get('organization', {}).get('city', ''),
            'state': person.get('organization', {}).get('state', ''),
            'country': person.get('organization', {}).get('country', ''),
            'linkedin_url': person.get('linkedin_url', ''),
            'source': 'apollo',
            'generated_at': datetime.now().isoformat()
        }
    
    def get_available_sources(self) -> List[Dict[str, str]]:
        """Get available lead generation sources"""
        sources = [
            {
                'id': 'gmaps',
                'name': 'Google Maps',
                'description': 'Generate leads from Google Maps business listings',
                'enabled': bool(self.client)
            },
            {
                'id': 'apollo',
                'name': 'Apollo',
                'description': 'Generate leads from Apollo.io database',
                'enabled': bool(self.apollo_api_key)
            }
        ]
        return sources