import os
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import google.generativeai as genai
from langchain.prompts import PromptTemplate

class LeadScoringService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY', 'your-google-api-key')
        self.model_name = 'gemini-2.0-flash'
        
        # Initialize Gemini
        if self.api_key != 'your-google-api-key':
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            print("Warning: Google API key not configured. Lead scoring will use fallback method.")
        
        # Define the scoring prompt template
        self.scoring_prompt = PromptTemplate(
            input_variables=["lead_data"],
            template="""
You are an AI lead scoring expert for a CBD throat spray company. Your job is to analyze lead data and provide a comprehensive score and assessment.

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
     * CBD-friendly industries (health, wellness, natural products, etc.): 20-25 points
     * Related industries (pharmaceuticals, supplements, etc.): 15-20 points
     * Neutral industries (retail, services, etc.): 10-15 points
     * Unrelated industries: 0-10 points
   
   - Company Size & Growth (20 points):
     * Large companies (1000+ employees): 15-20 points
     * Medium companies (100-999 employees): 10-15 points
     * Small companies (10-99 employees): 5-10 points
     * Very small companies (<10 employees): 0-5 points
   
   - Geographic Targeting (15 points):
     * CBD-friendly states/regions: 10-15 points
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

4. CBD-FRIENDLY INDUSTRIES:
   - Health & Wellness
   - Natural Products
   - Supplements & Vitamins
   - Alternative Medicine
   - Fitness & Sports
   - Beauty & Personal Care
   - Food & Beverage (natural/organic)
   - Retail (health/natural products)
   - Healthcare
   - Pharmaceuticals
   - Veterinary
   - Pet Care
   - Spa & Wellness
   - Yoga & Meditation
   - Nutrition
   - Herbal Medicine

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
    "recommendations": "<specific recommendations for this lead>",
    "confidence": "<HIGH|MEDIUM|LOW>",
    "reasoning": "<detailed explanation of the scoring decision>"
}}

Return ONLY the JSON object, no additional text or explanations.
"""
        )
    
    def score_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a lead based on comprehensive analysis using Gemini 2.0 Flash
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Dictionary containing score, status, factors, and recommendations
        """
        try:
            if not self.model:
                return self._fallback_scoring(lead_data)
            
            # Prepare lead data for analysis
            formatted_lead_data = self._format_lead_data(lead_data)
            
            # Generate scoring prompt
            prompt = self.scoring_prompt.format(lead_data=formatted_lead_data)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            scoring_result = self._parse_scoring_response(response.text)
            
            # Add metadata
            scoring_result['scored_at'] = datetime.now().isoformat()
            scoring_result['lead_id'] = lead_data.get('id')
            
            return scoring_result
            
        except Exception as e:
            print(f"Error scoring lead: {str(e)}")
            return self._fallback_scoring(lead_data)
    
    def _format_lead_data(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data for the AI prompt"""
        # Extract key information
        company_name = lead_data.get('company_name') or lead_data.get('name', 'Unknown')
        email = lead_data.get('email', 'Not provided')
        phone = lead_data.get('phone', 'Not provided')
        website = lead_data.get('website', 'Not provided')
        address = lead_data.get('address', 'Not provided')
        city = lead_data.get('city', 'Not provided')
        state = lead_data.get('state', 'Not provided')
        country = lead_data.get('country', 'Not provided')
        category = lead_data.get('category', 'Not provided')
        industry = lead_data.get('industry', 'Not provided')
        
        # Extract additional data from raw_data if available
        raw_data = lead_data.get('data', {}) or {}
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        # Get additional information from raw data
        employee_count = raw_data.get('employee_count') or raw_data.get('organization_headcount', 'Unknown')
        revenue = raw_data.get('revenue') or raw_data.get('organization_revenue_printed', 'Unknown')
        founded_year = raw_data.get('founded_year', 'Unknown')
        linkedin_url = raw_data.get('linkedin_url', 'Not provided')
        twitter_url = raw_data.get('twitter_url', 'Not provided')
        facebook_url = raw_data.get('facebook_url', 'Not provided')
        
        # Format the data
        formatted_data = f"""
COMPANY INFORMATION:
- Company Name: {company_name}
- Industry/Category: {category or industry}
- Founded Year: {founded_year}
- Employee Count: {employee_count}
- Revenue: {revenue}

CONTACT INFORMATION:
- Email: {email}
- Phone: {phone}
- Website: {website}

LOCATION:
- Address: {address}
- City: {city}
- State: {state}
- Country: {country}

ONLINE PRESENCE:
- LinkedIn: {linkedin_url}
- Twitter: {twitter_url}
- Facebook: {facebook_url}

ADDITIONAL DATA:
{json.dumps(raw_data, indent=2) if raw_data else 'No additional data available'}
"""
        
        return formatted_data
    
    def _parse_scoring_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response into structured scoring data"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate the response structure
                if 'score' not in result:
                    raise ValueError("Missing score in response")
                
                # Ensure score is within valid range
                result['score'] = max(0, min(100, int(result['score'])))
                
                # Determine status based on score
                if result['score'] >= 80:
                    result['status'] = 'HOT'
                elif result['score'] >= 60:
                    result['status'] = 'WARM'
                else:
                    result['status'] = 'COLD'
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing scoring response: {str(e)}")
            return self._fallback_scoring({})
    
    def _fallback_scoring(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback scoring method when AI is not available"""
        score = 0
        factors = {
            "contact_completeness": {"score": 0, "details": "Fallback scoring"},
            "industry_relevance": {"score": 0, "details": "Fallback scoring"},
            "company_size_growth": {"score": 0, "details": "Fallback scoring"},
            "geographic_targeting": {"score": 0, "details": "Fallback scoring"},
            "online_presence": {"score": 0, "details": "Fallback scoring"}
        }
        
        # Basic scoring logic
        if lead_data.get('email'):
            score += 10
            factors["contact_completeness"]["score"] += 10
        if lead_data.get('phone'):
            score += 10
            factors["contact_completeness"]["score"] += 10
        if lead_data.get('website'):
            score += 5
            factors["contact_completeness"]["score"] += 5
        
        # Industry relevance (basic)
        category = lead_data.get('category', '').lower()
        if any(term in category for term in ['health', 'wellness', 'natural', 'supplement', 'medical']):
            score += 20
            factors["industry_relevance"]["score"] += 20
        
        # Geographic targeting (basic)
        state = lead_data.get('state', '').lower()
        cbd_friendly_states = ['california', 'colorado', 'oregon', 'washington', 'nevada', 'alaska']
        if any(friendly_state in state for friendly_state in cbd_friendly_states):
            score += 10
            factors["geographic_targeting"]["score"] += 10
        
        # Determine status
        if score >= 80:
            status = 'HOT'
        elif score >= 60:
            status = 'WARM'
        else:
            status = 'COLD'
        
        return {
            "score": score,
            "status": status,
            "factors": factors,
            "recommendations": "Basic scoring applied due to AI unavailability",
            "confidence": "LOW",
            "reasoning": "Fallback scoring method used",
            "scored_at": datetime.now().isoformat(),
            "lead_id": lead_data.get('id')
        }
    
    def batch_score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score multiple leads in batch
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of scored leads
        """
        scored_leads = []
        
        for lead in leads:
            try:
                scored_lead = self.score_lead(lead)
                scored_leads.append({
                    **lead,
                    'scoring': scored_lead
                })
            except Exception as e:
                print(f"Error scoring lead {lead.get('id', 'unknown')}: {str(e)}")
                # Add default scoring for failed leads
                scored_leads.append({
                    **lead,
                    'scoring': self._fallback_scoring(lead)
                })
        
        return scored_leads
    
    def get_scoring_summary(self, scored_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of scored leads
        
        Args:
            scored_leads: List of leads with scoring data
            
        Returns:
            Summary statistics
        """
        if not scored_leads:
            return {
                "total_leads": 0,
                "hot_leads": 0,
                "warm_leads": 0,
                "cold_leads": 0,
                "average_score": 0,
                "score_distribution": {}
            }
        
        hot_count = sum(1 for lead in scored_leads if lead.get('scoring', {}).get('status') == 'HOT')
        warm_count = sum(1 for lead in scored_leads if lead.get('scoring', {}).get('status') == 'WARM')
        cold_count = sum(1 for lead in scored_leads if lead.get('scoring', {}).get('status') == 'COLD')
        
        scores = [lead.get('scoring', {}).get('score', 0) for lead in scored_leads]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_leads": len(scored_leads),
            "hot_leads": hot_count,
            "warm_leads": warm_count,
            "cold_leads": cold_count,
            "average_score": round(average_score, 2),
            "score_distribution": {
                "hot_percentage": round((hot_count / len(scored_leads)) * 100, 2),
                "warm_percentage": round((warm_count / len(scored_leads)) * 100, 2),
                "cold_percentage": round((cold_count / len(scored_leads)) * 100, 2)
            }
        } 