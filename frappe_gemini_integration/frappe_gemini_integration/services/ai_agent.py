import frappe
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
            frappe.logger().error(f"Error parsing criteria: {str(e)}")
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
        # Get configuration from Frappe settings
        self.settings = frappe.get_doc("Aida Lead Intelligence Settings")
        
        self.api_key = self.settings.get("google_api_key") or os.getenv('GOOGLE_API_KEY')
        self.model_name = 'gemini-2.0-flash'
        
        # Initialize Gemini
        if self.api_key and self.api_key != 'your-google-api-key':
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            frappe.logger().warning("Google API key not configured. Using fallback parsing.")
        
        self.criteria_parser = LeadCriteriaParser()
        
        # Define the prompt template for lead criteria extraction
        self.criteria_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""
            You are an AI assistant that extracts lead generation criteria from natural language queries.
            
            User Query: {user_query}
            
            Extract the following information and return it as a JSON object:
            - source: Lead generation source (gmaps, apollo) - default to 'gmaps'
            - search_terms: Array of business types/keywords to search for
            - location: Geographic location for the search
            - max_leads: Maximum number of leads to generate (default: 10)
            - language: Language code (default: 'en')
            - min_rating: Minimum rating filter (empty string if not specified)
            - skip_closed: Boolean - whether to skip closed businesses
            - require_email: Boolean - whether leads must have email addresses
            - require_phone: Boolean - whether leads must have phone numbers
            
            Examples:
            - "Find 20 restaurants in New York" → {{"source": "gmaps", "search_terms": ["restaurant"], "location": "New York, USA", "max_leads": 20}}
            - "Get tech companies in San Francisco with emails" → {{"source": "gmaps", "search_terms": ["tech company", "software company"], "location": "San Francisco, USA", "require_email": true}}
            
            Return only valid JSON.
            """
        )
    
    def extract_lead_criteria(self, user_query: str) -> Dict[str, Any]:
        """Extract lead generation criteria from natural language query"""
        try:
            if not self.model:
                return self._fallback_criteria_extraction(user_query)
            
            # Generate AI response
            prompt = self.criteria_prompt.format(user_query=user_query)
            response = self.model.generate_content(prompt)
            
            # Parse the response
            criteria = self.criteria_parser.parse(response.text)
            
            frappe.logger().info(f"Extracted criteria from query '{user_query}': {criteria}")
            return criteria
            
        except Exception as e:
            frappe.logger().error(f"Error extracting lead criteria: {str(e)}")
            # Fallback to basic parsing
            return self._fallback_criteria_extraction(user_query)
    
    def _fallback_criteria_extraction(self, user_query: str) -> Dict[str, Any]:
        """Fallback method for extracting lead criteria when AI is not available"""
        query_lower = user_query.lower()
        
        # Default criteria
        criteria = {
            'source': 'gmaps',
            'search_terms': ['business'],
            'location': 'United States',
            'max_leads': 10,
            'language': 'en',
            'min_rating': '',
            'skip_closed': False,
            'require_email': False,
            'require_phone': False
        }
        
        # Extract location
        location_keywords = ['in ', 'at ', 'near ', 'around ']
        for keyword in location_keywords:
            if keyword in query_lower:
                location_start = query_lower.find(keyword) + len(keyword)
                location_end = query_lower.find(',', location_start)
                if location_end == -1:
                    location_end = len(query_lower)
                location = user_query[location_start:location_end].strip()
                if location:
                    criteria['location'] = location
                break
        
        # Extract business type
        business_types = {
            'restaurant': ['restaurant', 'food', 'dining', 'cafe'],
            'tech': ['tech', 'technology', 'software', 'startup', 'it'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'clinic'],
            'retail': ['retail', 'store', 'shop', 'mall'],
            'finance': ['finance', 'bank', 'insurance', 'financial'],
            'manufacturing': ['manufacturing', 'factory', 'industrial']
        }
        
        for business_type, keywords in business_types.items():
            if any(keyword in query_lower for keyword in keywords):
                criteria['search_terms'] = [business_type]
                break
        
        # Extract number of leads
        import re
        number_match = re.search(r'(\d+)\s*(leads?|companies?|businesses?)', query_lower)
        if number_match:
            criteria['max_leads'] = int(number_match.group(1))
        
        # Check for specific requirements
        if 'email' in query_lower:
            criteria['require_email'] = True
        if 'phone' in query_lower:
            criteria['require_phone'] = True
        
        return criteria
    
    def analyze_lead_quality(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead quality and provide insights"""
        try:
            if not self.model:
                return self._fallback_quality_analysis(lead_data)
            
            prompt = f"""
            Analyze this lead data and provide quality insights:
            
            Lead Data: {json.dumps(lead_data, indent=2)}
            
            Provide analysis in JSON format:
            {{
                "quality_score": <0-100>,
                "strengths": ["list of strengths"],
                "weaknesses": ["list of weaknesses"],
                "recommendations": ["specific recommendations"],
                "priority": "<HIGH|MEDIUM|LOW>"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse response
            try:
                analysis = json.loads(response.text)
                return analysis
            except:
                return self._fallback_quality_analysis(lead_data)
                
        except Exception as e:
            frappe.logger().error(f"Error analyzing lead quality: {str(e)}")
            return self._fallback_quality_analysis(lead_data)
    
    def _fallback_quality_analysis(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback quality analysis when AI is not available"""
        score = 0
        strengths = []
        weaknesses = []
        
        # Basic scoring
        if lead_data.get('email'):
            score += 25
            strengths.append("Has email address")
        else:
            weaknesses.append("Missing email address")
        
        if lead_data.get('phone'):
            score += 25
            strengths.append("Has phone number")
        else:
            weaknesses.append("Missing phone number")
        
        if lead_data.get('website'):
            score += 15
            strengths.append("Has website")
        else:
            weaknesses.append("Missing website")
        
        if lead_data.get('company_name'):
            score += 15
            strengths.append("Company name available")
        else:
            weaknesses.append("Missing company name")
        
        if lead_data.get('industry'):
            score += 10
            strengths.append("Industry information available")
        
        if lead_data.get('city') and lead_data.get('state'):
            score += 10
            strengths.append("Location information complete")
        
        # Determine priority
        if score >= 80:
            priority = "HIGH"
        elif score >= 60:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        recommendations = []
        if not lead_data.get('email'):
            recommendations.append("Try to find email address through company website or LinkedIn")
        if not lead_data.get('phone'):
            recommendations.append("Search for company phone number online")
        if not lead_data.get('website'):
            recommendations.append("Verify if company has an online presence")
        
        return {
            "quality_score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "priority": priority
        }
    
    def generate_follow_up_suggestions(self, lead_data: Dict[str, Any], scoring_result: Dict[str, Any]) -> List[str]:
        """Generate follow-up suggestions based on lead data and scoring"""
        suggestions = []
        
        # Basic suggestions based on scoring
        if scoring_result.get('status') == 'HOT':
            suggestions.append("High priority lead - schedule immediate follow-up call")
            suggestions.append("Send personalized email with specific value proposition")
            suggestions.append("Research company for personalized outreach")
        elif scoring_result.get('status') == 'WARM':
            suggestions.append("Schedule follow-up call within 48 hours")
            suggestions.append("Send follow-up email with additional information")
            suggestions.append("Connect on LinkedIn for relationship building")
        else:
            suggestions.append("Send general follow-up email")
            suggestions.append("Add to nurture campaign")
            suggestions.append("Re-evaluate in 30 days")
        
        # Specific suggestions based on available data
        if lead_data.get('website'):
            suggestions.append("Review company website for specific pain points")
            suggestions.append("Check for recent news or updates about the company")
        
        if lead_data.get('industry'):
            suggestions.append(f"Research {lead_data['industry']} industry trends")
            suggestions.append("Prepare industry-specific case studies")
        
        if lead_data.get('city') and lead_data.get('state'):
            suggestions.append(f"Check for local events or meetups in {lead_data['city']}, {lead_data['state']}")
            suggestions.append("Research local market conditions")
        
        return suggestions