import os
from typing import Dict, Any, List
import json
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import google.generativeai as genai
from datetime import datetime
import re

class LeadCriteriaParser(BaseOutputParser):
    """Parse the LLM output into structured lead criteria"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse LLM response into structured criteria"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: parse manually
            criteria = {
                'source': 'gmaps',
                'search_terms': ['restaurant'],
                'location': 'New York, USA',
                'max_leads': 10,
                'language': 'en',
                'min_rating': '',
                'skip_closed': False,
                'require_email': False,
                'require_phone': False
            }
            
            # Extract information using regex patterns
            location_match = re.search(r'location["\s]*:["\s]*([^"\n,}]+)', text, re.IGNORECASE)
            if location_match:
                criteria['location'] = location_match.group(1).strip()
            
            # Extract search terms
            terms_match = re.search(r'search_terms["\s]*:["\s]*\[([^\]]+)\]', text, re.IGNORECASE)
            if terms_match:
                terms_str = terms_match.group(1)
                terms = [term.strip().strip('"') for term in terms_str.split(',')]
                criteria['search_terms'] = terms
            
            # Extract max leads
            max_match = re.search(r'max_leads["\s]*:["\s]*(\d+)', text, re.IGNORECASE)
            if max_match:
                criteria['max_leads'] = int(max_match.group(1))
            
            return criteria
            
        except Exception as e:
            print(f"Error parsing criteria: {str(e)}")
            # Return default criteria
            return {
                'source': 'gmaps',
                'search_terms': ['restaurant'],
                'location': 'New York, USA',
                'max_leads': 10,
                'language': 'en',
                'min_rating': '',
                'skip_closed': False,
                'require_email': False,
                'require_phone': False
            }

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY', 'your-google-api-key')
        self.model_name = 'gemini-2.0-flash'
        
        # Initialize Gemini
        if self.api_key != 'your-google-api-key':
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            print("Warning: Google API key not configured. Using fallback parsing.")
        
        self.criteria_parser = LeadCriteriaParser()
        
        # Define the prompt template for lead criteria extraction
        self.criteria_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""
            You are an AI assistant that extracts lead generation criteria from natural language queries.
            
            User Query: {user_query}
            
            Extract the following information and return it as a JSON object:
            - source: Lead generation source (gmaps, linkedin, apollo) - default to 'gmaps'
            - search_terms: Array of business types/keywords to search for
            - location: Geographic location for the search
            - max_leads: Maximum number of leads to generate (default: 10)
            - language: Language code (default: 'en')
            - min_rating: Minimum rating filter (empty string if not specified)
            - skip_closed: Boolean - whether to skip closed businesses
            - require_email: Boolean - whether leads must have email addresses
            - require_phone: Boolean - whether leads must have phone numbers
            
            Examples:
            Query: "Find 20 restaurants in Los Angeles with email addresses"
            Response: {{
                "source": "gmaps",
                "search_terms": ["restaurant"],
                "location": "Los Angeles, CA, USA",
                "max_leads": 20,
                "language": "en",
                "min_rating": "",
                "skip_closed": false,
                "require_email": true,
                "require_phone": false
            }}
            
            Query: "Get me 15 gyms and fitness centers in Miami with at least 4 stars"
            Response: {{
                "source": "gmaps",
                "search_terms": ["gym", "fitness center"],
                "location": "Miami, FL, USA",
                "max_leads": 15,
                "language": "en",
                "min_rating": "4",
                "skip_closed": false,
                "require_email": false,
                "require_phone": false
            }}
            
            Now extract criteria from the user query and return ONLY the JSON object:
            """
        )
    
    def extract_lead_criteria(self, user_query: str) -> Dict[str, Any]:
        """Extract lead generation criteria from natural language query"""
        try:
            if self.model:
                # Use Gemini model
                prompt = self.criteria_prompt.format(user_query=user_query)
                response = self.model.generate_content(prompt)
                criteria = self.criteria_parser.parse(response.text)
            else:
                # Fallback: simple keyword-based extraction
                criteria = self._fallback_extraction(user_query)
            
            # Validate and set defaults
            criteria = self._validate_criteria(criteria)
            
            return criteria
            
        except Exception as e:
            print(f"Error extracting criteria: {str(e)}")
            return self._get_default_criteria()
    
    def _fallback_extraction(self, user_query: str) -> Dict[str, Any]:
        """Fallback method for extracting criteria without AI model"""
        query_lower = user_query.lower()
        
        criteria = {
            'source': 'gmaps',
            'search_terms': [],
            'location': 'New York, USA',
            'max_leads': 10,
            'language': 'en',
            'min_rating': '',
            'skip_closed': False,
            'require_email': False,
            'require_phone': False
        }
        
        # Extract business types with better patterns
        business_types = {
            'restaurant': ['restaurant', 'restaurants', 'dining', 'eatery', 'eateries'],
            'cafe': ['cafe', 'cafes', 'coffee shop', 'coffee shops', 'coffee'],
            'gym': ['gym', 'gyms', 'fitness center', 'fitness centres', 'workout'],
            'hotel': ['hotel', 'hotels', 'motel', 'motels', 'accommodation'],
            'shop': ['shop', 'shops', 'store', 'stores', 'retail'],
            'clinic': ['clinic', 'clinics', 'medical center', 'health center'],
            'hospital': ['hospital', 'hospitals', 'medical facility'],
            'pharmacy': ['pharmacy', 'pharmacies', 'drugstore', 'chemist'],
            'bank': ['bank', 'banks', 'financial institution'],
            'salon': ['salon', 'salons', 'hair salon', 'beauty salon'],
            'spa': ['spa', 'spas', 'wellness center'],
            'lawyer': ['lawyer', 'lawyers', 'attorney', 'law firm'],
            'dentist': ['dentist', 'dentists', 'dental clinic', 'dental office'],
            'mechanic': ['mechanic', 'mechanics', 'auto repair', 'car repair'],
            'plumber': ['plumber', 'plumbers', 'plumbing service'],
            'electrician': ['electrician', 'electricians', 'electrical service']
        }
        
        found_types = []
        for main_type, variations in business_types.items():
            for variation in variations:
                if variation in query_lower:
                    found_types.append(main_type)
                    break
        
        # Remove duplicates while preserving order
        found_types = list(dict.fromkeys(found_types))
        
        if found_types:
            criteria['search_terms'] = found_types
        else:
            # Try to extract any quoted terms as business types
            quoted_terms = re.findall(r'"([^"]+)"', user_query)
            if quoted_terms:
                criteria['search_terms'] = quoted_terms
            else:
                criteria['search_terms'] = ['restaurant']  # default
        
        # Extract location with improved patterns
        location_patterns = [
            r'\bin\s+([A-Za-z][A-Za-z\s,.-]+?)(?:\s+(?:with|having|that|for|and|\d+)|$)',
            r'\bat\s+([A-Za-z][A-Za-z\s,.-]+?)(?:\s+(?:with|having|that|for|and|\d+)|$)',
            r'\bfrom\s+([A-Za-z][A-Za-z\s,.-]+?)(?:\s+(?:with|having|that|for|and|\d+)|$)',
            r'\bnear\s+([A-Za-z][A-Za-z\s,.-]+?)(?:\s+(?:with|having|that|for|and|\d+)|$)',
            r'\baround\s+([A-Za-z][A-Za-z\s,.-]+?)(?:\s+(?:with|having|that|for|and|\d+)|$)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                location = match.group(1).strip().rstrip(',')
                if len(location) > 2 and not any(word in location.lower() for word in ['with', 'having', 'that', 'for']):
                    criteria['location'] = location
                    break
        
        # Extract number of leads with better patterns
        number_patterns = [
            r'(\d+)\s*(?:leads?|businesses?|places?|results?|companies?)',
            r'(?:get|find|generate)\s+(\d+)',
            r'(?:up\s+to|maximum\s+of|max\s+of|limit\s+of)\s+(\d+)',
            r'(\d+)\s*(?:of|from)',
            r'\b(\d+)\s+(?:gym|gyms|restaurant|restaurants|cafe|cafes|hotel|hotels|shop|shops)',
            r'^(?:find|get|generate)?\s*(\d+)\s+',  # Match numbers at start like "Find 2 Gyms"
            r'\b(\d+)\s+\w+\s+in\s+'  # Match "2 gyms in" or "5 restaurants in"
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                num_leads = int(match.group(1))
                criteria['max_leads'] = num_leads
                break
        
        # Default max_leads is already set to 10 in criteria initialization
        
        # Check for email requirement
        if any(word in query_lower for word in ['email', 'emails', 'email address']):
            criteria['require_email'] = True
        
        # Check for phone requirement
        if any(word in query_lower for word in ['phone', 'phones', 'phone number', 'contact']):
            criteria['require_phone'] = True
        
        # Check for rating requirement
        rating_match = re.search(r'(\d+)\s*(?:star|stars|rating)', query_lower)
        if rating_match:
            criteria['min_rating'] = rating_match.group(1)
        
        return criteria
    
    def _validate_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set defaults for criteria"""
        defaults = {
            'source': 'gmaps',
            'search_terms': ['restaurant'],
            'location': 'New York, USA',
            'max_leads': 10,
            'language': 'en',
            'min_rating': '',
            'skip_closed': False,
            'require_email': False,
            'require_phone': False
        }
        
        # Ensure all required fields exist
        for key, default_value in defaults.items():
            if key not in criteria:
                criteria[key] = default_value
        
        # Validate data types and ranges
        criteria['max_leads'] = max(1, min(int(criteria.get('max_leads', 10)), 50))
        
        if not isinstance(criteria.get('search_terms'), list):
            criteria['search_terms'] = ['restaurant']
        
        if not criteria.get('search_terms'):
            criteria['search_terms'] = ['restaurant']
        
        return criteria
    
    def _get_default_criteria(self) -> Dict[str, Any]:
        """Get default lead generation criteria"""
        return {
            'source': 'gmaps',
            'search_terms': ['restaurant'],
            'location': 'New York, USA',
            'max_leads': 10,
            'language': 'en',
            'min_rating': '',
            'skip_closed': False,
            'require_email': False,
            'require_phone': False
        }
    
    def generate_email_template(self, company_info: Dict[str, Any], 
                              lead_info: Dict[str, Any], 
                              template_type: str = 'general') -> str:
        """Generate personalized email content (for future outreach feature)"""
        # This will be implemented in the outreach phase
        # For now, return a placeholder
        return f"""Subject: Partnership Opportunity with {company_info.get('name', 'Our Company')}
        
Dear {lead_info.get('company_name', 'Business Owner')},

I hope this email finds you well. I'm reaching out from {company_info.get('name', 'Our Company')} 
because I believe there might be a great opportunity for us to work together.

[Personalized content will be generated here based on lead information]

Best regards,
{company_info.get('contact_name', 'Your Name')}
{company_info.get('email', 'your-email@company.com')}
{company_info.get('phone', 'your-phone-number')}
"""