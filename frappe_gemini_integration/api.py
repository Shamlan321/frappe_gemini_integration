import frappe
from frappe import _
from frappe.utils import now_datetime, get_url
import json
from typing import Dict, Any, List
from datetime import datetime

# Import services
from .frappe_gemini_integration.services import (
    LeadGenerator, 
    LeadScoringService, 
    AIAgent, 
    ERPIntegration
)

@frappe.whitelist()
def generate_leads(user_query: str, source: str = "gmaps", max_leads: int = 10, **kwargs):
    """Generate leads based on user query"""
    try:
        # Initialize services
        ai_agent = AIAgent()
        lead_generator = LeadGenerator()
        
        # Extract lead generation criteria using AI
        criteria = ai_agent.extract_lead_criteria(user_query)
        criteria['source'] = source
        criteria['max_leads'] = max_leads
        
        # Override with any additional parameters
        for key, value in kwargs.items():
            if value:
                criteria[key] = value
        
        # Generate leads
        leads = lead_generator.generate_leads(criteria)
        
        # Save lead generation record
        lead_history = frappe.get_doc({
            'doctype': 'Aida Lead Generation History',
            'user_query': user_query,
            'source': source,
            'criteria': json.dumps(criteria),
            'leads_generated': len(leads),
            'status': 'Completed'
        })
        lead_history.insert()
        
        # Save individual leads
        saved_leads = []
        for lead_data in leads:
            lead_doc = frappe.get_doc({
                'doctype': 'Aida Generated Lead',
                'lead_generation_history': lead_history.name,
                'company_name': lead_data.get('company_name', ''),
                'first_name': lead_data.get('first_name', ''),
                'last_name': lead_data.get('last_name', ''),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'website': lead_data.get('website', ''),
                'title': lead_data.get('title', ''),
                'industry': lead_data.get('industry', ''),
                'company_size': lead_data.get('company_size', ''),
                'city': lead_data.get('city', ''),
                'state': lead_data.get('state', ''),
                'country': lead_data.get('country', ''),
                'address': lead_data.get('address', ''),
                'rating': lead_data.get('rating', 0),
                'reviews_count': lead_data.get('reviews_count', 0),
                'category': lead_data.get('category', ''),
                'latitude': lead_data.get('latitude', 0),
                'longitude': lead_data.get('longitude', 0),
                'linkedin_url': lead_data.get('linkedin_url', ''),
                'source': lead_data.get('source', source),
                'generated_at': lead_data.get('generated_at', now_datetime().isoformat())
            })
            lead_doc.insert()
            saved_leads.append(lead_doc.name)
        
        return {
            'success': True,
            'message': f'Generated {len(leads)} leads successfully',
            'leads': leads,
            'criteria': criteria,
            'lead_history_id': lead_history.name,
            'saved_lead_ids': saved_leads
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating leads: {str(e)}", "Lead Generation")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def score_lead(lead_id: str):
    """Score a single lead using AI"""
    try:
        # Get the lead data
        lead_doc = frappe.get_doc("Aida Generated Lead", lead_id)
        if not lead_doc:
            return {
                'success': False,
                'error': 'Lead not found'
            }
        
        # Convert to dictionary for scoring
        lead_data = lead_doc.as_dict()
        
        # Initialize scoring service
        scoring_service = LeadScoringService()
        
        # Score the lead
        scoring_result = scoring_service.score_lead(lead_data)
        
        # Save the score
        score_doc = frappe.get_doc({
            'doctype': 'Aida Lead Score',
            'lead': lead_id,
            'score': scoring_result.get('score', 0),
            'status': scoring_result.get('status', 'COLD'),
            'scoring_factors': json.dumps(scoring_result.get('factors', {})),
            'summary': scoring_result.get('summary', ''),
            'recommendations': json.dumps(scoring_result.get('recommendations', [])),
            'risk_factors': scoring_result.get('risk_factors', ''),
            'scoring_method': scoring_result.get('scoring_method', 'ai_gemini'),
            'scored_at': scoring_result.get('scored_at', now_datetime().isoformat())
        })
        score_doc.insert()
        
        # Update lead with score
        lead_doc.lead_score = score_doc.name
        lead_doc.score = scoring_result.get('score', 0)
        lead_doc.status = scoring_result.get('status', 'COLD')
        lead_doc.save()
        
        return {
            'success': True,
            'message': 'Lead scored successfully',
            'scoring': scoring_result,
            'score_id': score_doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error scoring lead: {str(e)}", "Lead Scoring")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def batch_score_leads(lead_ids: List[str]):
    """Score multiple leads in batch"""
    try:
        if not isinstance(lead_ids, list):
            lead_ids = json.loads(lead_ids)
        
        scoring_service = LeadScoringService()
        results = []
        
        for lead_id in lead_ids:
            try:
                result = score_lead(lead_id)
                results.append({
                    'lead_id': lead_id,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'lead_id': lead_id,
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        return {
            'success': True,
            'message': f'Scored {len(lead_ids)} leads',
            'results': results
        }
        
    except Exception as e:
        frappe.log_error(f"Error batch scoring leads: {str(e)}", "Lead Scoring")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_lead_sources():
    """Get available lead generation sources"""
    try:
        lead_generator = LeadGenerator()
        sources = lead_generator.get_available_sources()
        
        return {
            'success': True,
            'sources': sources
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting lead sources: {str(e)}", "Lead Sources")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def test_erp_connection(erp_url: str = None, erp_username: str = None, erp_password: str = None):
    """Test ERP connection"""
    try:
        erp_integration = ERPIntegration()
        
        if erp_url and erp_username and erp_password:
            # Test with provided credentials
            config = {
                'url': erp_url,
                'username': erp_username,
                'password': erp_password
            }
            result = erp_integration.test_connection_with_config(config)
        else:
            # Test with saved configuration
            result = erp_integration.test_connection()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error testing ERP connection: {str(e)}", "ERP Integration")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def sync_lead_to_erp(lead_id: str):
    """Sync a lead to ERP system"""
    try:
        # Get the lead data
        lead_doc = frappe.get_doc("Aida Generated Lead", lead_id)
        if not lead_doc:
            return {
                'success': False,
                'error': 'Lead not found'
            }
        
        # Convert to dictionary
        lead_data = lead_doc.as_dict()
        
        # Initialize ERP integration
        erp_integration = ERPIntegration()
        
        # Create lead in ERP
        result = erp_integration.create_lead_in_erp(lead_data)
        
        if result.get('success'):
            # Update lead with ERP ID
            lead_doc.erp_lead_id = result.get('erp_lead_id')
            lead_doc.synced_to_erp = True
            lead_doc.synced_at = now_datetime()
            lead_doc.save()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error syncing lead to ERP: {str(e)}", "ERP Integration")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = {}
        
        # Get lead generation statistics
        lead_history_count = frappe.db.count("Aida Lead Generation History")
        total_leads_generated = frappe.db.count("Aida Generated Lead")
        
        # Get scoring statistics
        scored_leads_count = frappe.db.count("Aida Lead Score")
        
        # Get ERP sync statistics
        synced_leads_count = frappe.db.count("Aida Generated Lead", {"synced_to_erp": 1})
        
        # Get leads by status
        leads_by_status = frappe.db.sql("""
            SELECT status, COUNT(*) as count
            FROM `tabAida Generated Lead`
            GROUP BY status
        """, as_dict=True)
        
        # Get leads by source
        leads_by_source = frappe.db.sql("""
            SELECT source, COUNT(*) as count
            FROM `tabAida Generated Lead`
            GROUP BY source
        """, as_dict=True)
        
        stats.update({
            'lead_generation': {
                'total_sessions': lead_history_count,
                'total_leads': total_leads_generated
            },
            'lead_scoring': {
                'scored_leads': scored_leads_count,
                'scoring_rate': (scored_leads_count / total_leads_generated * 100) if total_leads_generated > 0 else 0
            },
            'erp_integration': {
                'synced_leads': synced_leads_count,
                'sync_rate': (synced_leads_count / total_leads_generated * 100) if total_leads_generated > 0 else 0
            },
            'leads_by_status': {item.status: item.count for item in leads_by_status},
            'leads_by_source': {item.source: item.count for item in leads_by_source}
        })
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dashboard stats: {str(e)}", "Dashboard")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_leads(filters: Dict[str, Any] = None, page_length: int = 20, page_start: int = 0):
    """Get leads with optional filtering"""
    try:
        if not filters:
            filters = {}
        
        # Build filters for database query
        db_filters = {}
        if filters.get('status'):
            db_filters['status'] = filters['status']
        if filters.get('source'):
            db_filters['source'] = filters['source']
        if filters.get('company_name'):
            db_filters['company_name'] = ['like', f"%{filters['company_name']}%"]
        
        # Get leads
        leads = frappe.get_list(
            "Aida Generated Lead",
            filters=db_filters,
            fields=["*"],
            limit_start=page_start,
            limit_page_length=page_length,
            order_by="creation desc"
        )
        
        # Get total count
        total_count = frappe.db.count("Aida Generated Lead", db_filters)
        
        return {
            'success': True,
            'leads': leads,
            'total_count': total_count,
            'page_length': page_length,
            'page_start': page_start
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting leads: {str(e)}", "Lead Management")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def delete_lead(lead_id: str):
    """Delete a lead"""
    try:
        lead_doc = frappe.get_doc("Aida Generated Lead", lead_id)
        if not lead_doc:
            return {
                'success': False,
                'error': 'Lead not found'
            }
        
        # Delete associated score if exists
        if lead_doc.lead_score:
            try:
                frappe.delete_doc("Aida Lead Score", lead_doc.lead_score)
            except:
                pass
        
        # Delete the lead
        frappe.delete_doc("Aida Generated Lead", lead_id)
        
        return {
            'success': True,
            'message': 'Lead deleted successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error deleting lead: {str(e)}", "Lead Management")
        return {
            'success': False,
            'error': str(e)
        }
