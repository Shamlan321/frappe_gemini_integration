from apify_client import ApifyClient
import os
from typing import List, Dict, Any
import json
from datetime import datetime
import http.client
import requests

class LeadGenerator:
    def __init__(self):
        self.apify_token = os.getenv('APIFY_TOKEN', 'apify_api_8ViThYsJGuDpcAQXNzKKdem6umJJS20PdRUV')
        self.client = ApifyClient(self.apify_token)
        
        # Google Maps Actor ID
        self.gmaps_actor_id = "WnMxbsRLNbPeYL6ge"
        
        # Apollo API configuration
        self.apollo_api_key = os.getenv('APOLLO_API_KEY', '43f2dbba86msh05ddb7cb80b229ap1b9d62jsnb2521509938c')
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
            print(f"\n=== GOOGLE MAPS LEAD GENERATION ===")
            print(f"Input criteria: {criteria}")
            
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
                print("Filter: Only businesses with email addresses")
            if criteria.get('require_phone', False):
                run_input["onlyDataWithPhones"] = True
                print("Filter: Only businesses with phone numbers")
            
            print(f"\nApify Actor Input:")
            for key, value in run_input.items():
                print(f"  {key}: {value}")
            
            print(f"\nRunning Google Maps actor (ID: {self.gmaps_actor_id})...")
            
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.gmaps_actor_id).call(run_input=run_input)
            print(f"Actor run completed. Dataset ID: {run['defaultDatasetId']}")
            
            # Fetch and process results
            leads = []
            item_count = 0
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                item_count += 1
                lead = self._process_gmaps_lead(item)
                leads.append(lead)
                print(f"Processed lead {item_count}: {lead.get('company_name', 'Unknown')} in {lead.get('city', 'Unknown location')}")
            
            print(f"\n=== LEAD GENERATION COMPLETE ===")
            print(f"Total leads generated: {len(leads)}")
            print(f"Search terms used: {criteria.get('search_terms')}")
            print(f"Location searched: {criteria.get('location')}")
            print(f"Max leads requested: {criteria.get('max_leads')}")
            
            return leads
            
        except Exception as e:
            print(f"\n❌ ERROR generating Google Maps leads: {str(e)}")
            print(f"Criteria that caused error: {criteria}")
            raise
    
    def _generate_apollo_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate leads from Apollo API"""
        try:
            print(f"\n=== APOLLO LEAD GENERATION ===")
            print(f"Input criteria: {criteria}")
            
            url = criteria.get('url', '')
            page = criteria.get('page', 1)
            
            if not url:
                raise ValueError("Apollo URL is required")
            
            # Prepare the API request
            payload = {
                "url": url,
                "page": page
            }
            
            headers = {
                'x-rapidapi-key': self.apollo_api_key,
                'x-rapidapi-host': self.apollo_host,
                'Content-Type': "application/json"
            }
            
            print(f"\nMaking Apollo API request...")
            print(f"URL: {url}")
            print(f"Page: {page}")
            
            # Make the API request
            response = requests.post(
                f"https://{self.apollo_host}/search_organizations_via_url",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Apollo API request failed with status {response.status_code}: {response.text}")
            
            data = response.json()
            print(f"Apollo API response received")
            
            # Process the organizations
            organizations = data.get('data', {}).get('organizations', [])
            leads = []
            
            for org in organizations:
                lead = self._process_apollo_lead(org)
                leads.append(lead)
                print(f"Processed Apollo lead: {lead.get('company_name', 'Unknown')}")
            
            print(f"\n=== APOLLO LEAD GENERATION COMPLETE ===")
            print(f"Total leads generated: {len(leads)}")
            print(f"URL used: {url}")
            print(f"Page requested: {page}")
            
            return leads
            
        except Exception as e:
            print(f"\n❌ ERROR generating Apollo leads: {str(e)}")
            print(f"Criteria that caused error: {criteria}")
            raise
    
    def _process_gmaps_lead(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Google Maps data into standardized lead format"""
        # Extract contact information
        emails = raw_data.get('emails', [])
        phones = raw_data.get('phones', [])
        
        # Get primary contact info
        primary_email = emails[0] if emails else ''
        primary_phone = phones[0] if phones else ''
        
        # Extract address components
        address_obj = raw_data.get('address', {})
        full_address = ''
        if isinstance(address_obj, dict):
            address_parts = [
                address_obj.get('streetNumber', ''),
                address_obj.get('streetName', ''),
                address_obj.get('city', ''),
                address_obj.get('state', ''),
                address_obj.get('postalCode', '')
            ]
            full_address = ', '.join([part for part in address_parts if part])
        elif isinstance(address_obj, str):
            full_address = address_obj
        
        # Create standardized lead object
        lead = {
            'source': 'Google Maps',
            'company_name': raw_data.get('title', ''),
            'email': primary_email,
            'phone': primary_phone,
            'website': raw_data.get('website', ''),
            'address': full_address,
            'city': address_obj.get('city', '') if isinstance(address_obj, dict) else '',
            'state': address_obj.get('state', '') if isinstance(address_obj, dict) else '',
            'country': address_obj.get('country', '') if isinstance(address_obj, dict) else '',
            'postal_code': address_obj.get('postalCode', '') if isinstance(address_obj, dict) else '',
            'rating': raw_data.get('totalScore', 0),
            'review_count': raw_data.get('reviewsCount', 0),
            'category': raw_data.get('categoryName', ''),
            'description': raw_data.get('description', ''),
            'google_maps_url': raw_data.get('url', ''),
            'place_id': raw_data.get('placeId', ''),
            'latitude': raw_data.get('location', {}).get('lat', 0),
            'longitude': raw_data.get('location', {}).get('lng', 0),
            'social_media': {
                'instagram': raw_data.get('instagrams', []),
                'facebook': raw_data.get('facebooks', []),
                'twitter': raw_data.get('twitters', []),
                'linkedin': raw_data.get('linkedIns', []),
                'youtube': raw_data.get('youtubes', [])
            },
            'business_hours': raw_data.get('openingHours', []),
            'additional_info': raw_data.get('additionalInfo', {}),
            'generated_at': datetime.now().isoformat(),
            'raw_data': raw_data  # Store complete raw data for reference
        }
        
        return lead
    
    def _process_apollo_lead(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Apollo data into standardized lead format"""
        # Extract primary contact information
        primary_phone = raw_data.get('primary_phone', {})
        phone_number = primary_phone.get('number', '') if isinstance(primary_phone, dict) else raw_data.get('phone', '')
        
        # Extract address information
        address_parts = []
        if raw_data.get('address'):
            address_obj = raw_data['address']
            if isinstance(address_obj, dict):
                address_parts = [
                    address_obj.get('street', ''),
                    address_obj.get('city', ''),
                    address_obj.get('state', ''),
                    address_obj.get('country', ''),
                    address_obj.get('zip', '')
                ]
            elif isinstance(address_obj, str):
                address_parts = [address_obj]
        
        full_address = ', '.join([part for part in address_parts if part])
        
        # Create standardized lead object
        lead = {
            'source': 'Apollo',
            'company_name': raw_data.get('name', ''),
            'email': '',  # Apollo doesn't provide emails in organization search
            'phone': phone_number,
            'website': raw_data.get('website_url', ''),
            'address': full_address,
            'city': raw_data.get('address', {}).get('city', '') if isinstance(raw_data.get('address'), dict) else '',
            'state': raw_data.get('address', {}).get('state', '') if isinstance(raw_data.get('address'), dict) else '',
            'country': raw_data.get('address', {}).get('country', '') if isinstance(raw_data.get('address'), dict) else '',
            'postal_code': raw_data.get('address', {}).get('zip', '') if isinstance(raw_data.get('address'), dict) else '',
            'rating': 0,  # Apollo doesn't provide ratings
            'review_count': 0,
            'category': raw_data.get('industry', ''),
            'description': raw_data.get('description', ''),
            'linkedin_url': raw_data.get('linkedin_url', ''),
            'twitter_url': raw_data.get('twitter_url', ''),
            'facebook_url': raw_data.get('facebook_url', ''),
            'founded_year': raw_data.get('founded_year', ''),
            'employee_count': raw_data.get('organization_headcount', ''),
            'revenue': raw_data.get('organization_revenue_printed', ''),
            'revenue_amount': raw_data.get('organization_revenue', 0),
            'market_cap': raw_data.get('market_cap', ''),
            'publicly_traded_symbol': raw_data.get('publicly_traded_symbol', ''),
            'publicly_traded_exchange': raw_data.get('publicly_traded_exchange', ''),
            'languages': raw_data.get('languages', []),
            'alexa_ranking': raw_data.get('alexa_ranking', ''),
            'logo_url': raw_data.get('logo_url', ''),
            'crunchbase_url': raw_data.get('crunchbase_url', ''),
            'angellist_url': raw_data.get('angellist_url', ''),
            'blog_url': raw_data.get('blog_url', ''),
            'primary_domain': raw_data.get('primary_domain', ''),
            'owned_by_organization': raw_data.get('owned_by_organization', {}),
            'organization_headcount_growth': {
                'six_month': raw_data.get('organization_headcount_six_month_growth', 0),
                'twelve_month': raw_data.get('organization_headcount_twelve_month_growth', 0),
                'twenty_four_month': raw_data.get('organization_headcount_twenty_four_month_growth', 0)
            },
            'intent_strength': raw_data.get('intent_strength', ''),
            'show_intent': raw_data.get('show_intent', False),
            'has_intent_signal_account': raw_data.get('has_intent_signal_account', False),
            'generated_at': datetime.now().isoformat(),
            'raw_data': raw_data  # Store complete raw data for reference
        }
        
        return lead
    
    def get_available_sources(self) -> List[Dict[str, str]]:
        """Get list of available lead generation sources"""
        return [
            {
                'id': 'gmaps',
                'name': 'Google Maps',
                'description': 'Generate leads from Google Maps business listings',
                'status': 'active'
            },
            {
                'id': 'apollo',
                'name': 'Apollo',
                'description': 'Generate leads using Apollo API',
                'status': 'active'
            },
            {
                'id': 'linkedin',
                'name': 'LinkedIn',
                'description': 'Generate leads from LinkedIn profiles and companies',
                'status': 'coming_soon'
            }
        ]