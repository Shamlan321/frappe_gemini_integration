import frappe
import os
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import google.generativeai as genai
from langchain.prompts import PromptTemplate

class LeadScoringService:
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
            frappe.logger().warning("Google API key not configured. Lead scoring will use fallback method.")
        
        # Define the scoring prompt template
        self.scoring_prompt = PromptTemplate(
            input_variables=["lead_data"],
            template="""
You are an AI lead scoring expert for a business lead intelligence platform. Your job is to analyze lead data and provide a comprehensive score and assessment.

LEAD SCORING GUIDELINES:

1. SCORE RANGES:
   - HOT (80-100): High-quality leads with complete information, relevant industry, and strong potential
   - WARM (60-79): Good leads with decent information and moderate potential
   - COLD (0-59): Low-quality leads with incomplete information or low potential

2. SCORING FACTORS (Total 100 points):
   - Contact Information Completeness (25 points):
     * Email address: 10 points
     * Phone number: 10 points
     * Website: 5 points
   
   - Industry Relevance (25 points):
     * High-potential industries (tech, healthcare, finance, etc.): 20-25 points
     * Related industries: 15-20 points
     * Neutral industries: 10-15 points
     * Unrelated industries: 0-10 points
   
   - Company Size & Growth (20 points):
     * Large companies (1000+ employees): 15-20 points
     * Medium companies (100-999 employees): 10-15 points
     * Small companies (10-99 employees): 5-10 points
     * Very small companies (<10 employees): 0-5 points
   
   - Geographic Targeting (15 points):
     * Target markets: 10-15 points
     * Neutral regions: 5-10 points
     * Restricted regions: 0-5 points
   
   - Online Presence & Engagement (15 points):
     * Strong social media presence: 10-15 points
     * Basic online presence: 5-10 points
     * Limited online presence: 0-5 points

3. ADDITIONAL FACTORS:
   - Revenue potential (high revenue companies get bonus points)
   - Growth indicators (companies showing growth get bonus points)
   - Regulatory compliance (companies in regulated industries get bonus points)
   - Market position (established companies get bonus points)

LEAD DATA TO ANALYZE:
{lead_data}

Please analyze this lead and provide a JSON response with the following structure:
{{
    "score": <integer between 0-100>,
    "status": "<HOT|WARM|COLD>",
    "factors": {{
        "contact_completeness": {{
            "score": <integer 0-25>,
            "details": "<explanation>"
        }},
        "industry_relevance": {{
            "score": <integer 0-25>,
            "details": "<explanation>"
        }},
        "company_size_growth": {{
            "score": <integer 0-20>,
            "details": "<explanation>"
        }},
        "geographic_targeting": {{
            "score": <integer 0-15>,
            "details": "<explanation>"
        }},
        "online_presence": {{
            "score": <integer 0-15>,
            "details": "<explanation>"
        }}
    }},
    "summary": "<brief summary of the lead quality>",
    "recommendations": "<specific recommendations for follow-up>",
    "risk_factors": "<any potential risks or concerns>"
}}

Ensure the response is valid JSON and all scores add up to the total score.
"""
        )
    
    def score_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single lead using AI"""
        try:
            if not self.model:
                return self._fallback_scoring(lead)
            
            # Prepare lead data for analysis
            lead_data = self._format_lead_data(lead)
            
            # Generate AI response
            prompt = self.scoring_prompt.format(lead_data=lead_data)
            response = self.model.generate_content(prompt)
            
            # Parse the response
            scoring_result = self._parse_ai_response(response.text)
            
            # Add metadata
            scoring_result['scored_at'] = datetime.now().isoformat()
            scoring_result['lead_id'] = lead.get('name', '')
            scoring_result['scoring_method'] = 'ai_gemini'
            
            frappe.logger().info(f"Lead {lead.get('name', 'Unknown')} scored: {scoring_result.get('score', 'N/A')}")
            return scoring_result
            
        except Exception as e:
            frappe.log_error(f"Error scoring lead: {str(e)}", "Lead Scoring")
            # Fallback to basic scoring
            return self._fallback_scoring(lead)
    
    def _format_lead_data(self, lead: Dict[str, Any]) -> str:
        """Format lead data for AI analysis"""
        formatted_data = []
        
        # Basic company information
        if lead.get('company_name'):
            formatted_data.append(f"Company: {lead['company_name']}")
        if lead.get('industry'):
            formatted_data.append(f"Industry: {lead['industry']}")
        if lead.get('company_size'):
            formatted_data.append(f"Company Size: {lead['company_size']}")
        
        # Contact information
        contact_info = []
        if lead.get('email'):
            contact_info.append(f"Email: {lead['email']}")
        if lead.get('phone'):
            contact_info.append(f"Phone: {lead['phone']}")
        if lead.get('website'):
            contact_info.append(f"Website: {lead['website']}")
        
        if contact_info:
            formatted_data.append("Contact Information:")
            formatted_data.extend([f"  {info}" for info in contact_info])
        
        # Location information
        location_parts = []
        if lead.get('city'):
            location_parts.append(lead['city'])
        if lead.get('state'):
            location_parts.append(lead['state'])
        if lead.get('country'):
            location_parts.append(lead['country'])
        
        if location_parts:
            formatted_data.append(f"Location: {', '.join(location_parts)}")
        
        # Additional details
        if lead.get('title'):
            formatted_data.append(f"Contact Title: {lead['title']}")
        if lead.get('rating'):
            formatted_data.append(f"Rating: {lead['rating']}")
        if lead.get('source'):
            formatted_data.append(f"Source: {lead['source']}")
        
        return "\n".join(formatted_data)
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract scoring data"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            frappe.logger().error(f"Error parsing AI response: {str(e)}")
            # Return fallback scoring
            return self._fallback_scoring({})
    
    def _fallback_scoring(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback scoring method when AI is not available"""
        score = 0
        factors = {}
        
        # Contact completeness (25 points)
        contact_score = 0
        if lead.get('email'):
            contact_score += 10
        if lead.get('phone'):
            contact_score += 10
        if lead.get('website'):
            contact_score += 5
        factors['contact_completeness'] = {
            'score': contact_score,
            'details': f"Email: {'Yes' if lead.get('email') else 'No'}, Phone: {'Yes' if lead.get('phone') else 'No'}, Website: {'Yes' if lead.get('website') else 'No'}"
        }
        score += contact_score
        
        # Industry relevance (25 points)
        industry_score = 15  # Default neutral score
        if lead.get('industry'):
            industry_lower = lead['industry'].lower()
            if any(keyword in industry_lower for keyword in ['tech', 'software', 'healthcare', 'finance']):
                industry_score = 20
            elif any(keyword in industry_lower for keyword in ['retail', 'service', 'manufacturing']):
                industry_score = 15
            else:
                industry_score = 10
        
        factors['industry_relevance'] = {
            'score': industry_score,
            'details': f"Industry: {lead.get('industry', 'Unknown')} - scored based on market potential"
        }
        score += industry_score
        
        # Company size (20 points)
        size_score = 10  # Default medium company score
        if lead.get('company_size'):
            try:
                size = int(str(lead['company_size']).replace(',', ''))
                if size >= 1000:
                    size_score = 18
                elif size >= 100:
                    size_score = 15
                elif size >= 10:
                    size_score = 10
                else:
                    size_score = 5
            except:
                size_score = 10
        
        factors['company_size_growth'] = {
            'score': size_score,
            'details': f"Company size: {lead.get('company_size', 'Unknown')} - scored based on employee count"
        }
        score += size_score
        
        # Geographic targeting (15 points)
        geo_score = 10  # Default neutral score
        if lead.get('country') and lead.get('country').lower() in ['united states', 'usa', 'us', 'canada', 'uk', 'germany']:
            geo_score = 12
        
        factors['geographic_targeting'] = {
            'score': geo_score,
            'details': f"Location: {lead.get('city', '')}, {lead.get('state', '')}, {lead.get('country', '')}"
        }
        score += geo_score
        
        # Online presence (15 points)
        online_score = 8  # Default basic presence score
        if lead.get('website'):
            online_score += 5
        if lead.get('linkedin_url'):
            online_score += 2
        
        factors['online_presence'] = {
            'score': min(online_score, 15),
            'details': f"Website: {'Yes' if lead.get('website') else 'No'}, LinkedIn: {'Yes' if lead.get('linkedin_url') else 'No'}"
        }
        score += min(online_score, 15)
        
        # Determine status
        if score >= 80:
            status = "HOT"
        elif score >= 60:
            status = "WARM"
        else:
            status = "COLD"
        
        return {
            'score': score,
            'status': status,
            'factors': factors,
            'summary': f"Lead scored {score}/100 using fallback method",
            'recommendations': "Consider manual review for more accurate assessment",
            'risk_factors': "Limited data available for comprehensive scoring",
            'scored_at': datetime.now().isoformat(),
            'scoring_method': 'fallback'
        }
    
    def batch_score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple leads in batch"""
        scored_leads = []
        
        for lead in leads:
            try:
                scoring_result = self.score_lead(lead)
                scored_leads.append({
                    'lead': lead,
                    'scoring': scoring_result
                })
            except Exception as e:
                frappe.log_error(f"Error scoring lead {lead.get('name', 'Unknown')}: {str(e)}", "Lead Scoring")
                continue
        
        return scored_leads