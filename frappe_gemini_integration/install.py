import frappe
from frappe import _
from frappe.utils import now_datetime

def after_install():
    """Setup tasks to run after app installation"""
    try:
        # Create default settings
        create_default_settings()
        
        # Create default dashboard page
        create_dashboard_page()
        
        # Set up permissions
        setup_permissions()
        
        # Create initial data
        create_initial_data()
        
        frappe.msgprint(_("Aida Lead Intelligence app installed successfully!"), alert=True)
        
    except Exception as e:
        frappe.log_error(f"Error during Aida Lead Intelligence installation: {str(e)}")
        frappe.throw(_("Installation completed with errors. Please check the error log."))

def create_default_settings():
    """Create default app settings"""
    if not frappe.db.exists("Aida Lead Intelligence Settings"):
        settings = frappe.get_doc({
            "doctype": "Aida Lead Intelligence Settings",
            "company_name": "Your Company",
            "industry": "Technology",
            "website": "https://yourcompany.com",
            "description": "AI-Powered Lead Generation and Intelligence Platform"
        })
        settings.insert()
        frappe.db.commit()

def create_dashboard_page():
    """Create the dashboard page"""
    if not frappe.db.exists("Page", "aida-dashboard"):
        page = frappe.get_doc({
            "doctype": "Page",
            "page_name": "aida-dashboard",
            "title": "Aida Lead Intelligence Dashboard",
            "dashboard_title": "Aida Lead Intelligence Dashboard",
            "dashboard_description": "AI-Powered Lead Generation and Intelligence Platform",
            "dashboard_type": "Page",
            "is_standard": 1,
            "module": "Aida Lead Intelligence"
        })
        page.insert()
        frappe.db.commit()

def setup_permissions():
    """Set up basic permissions"""
    # Create role if it doesn't exist
    if not frappe.db.exists("Role", "Aida Lead Intelligence User"):
        role = frappe.get_doc({
            "doctype": "Role",
            "role_name": "Aida Lead Intelligence User",
            "desk_access": 1,
            "restrict_to_domain": "",
            "two_factor_auth": 0,
            "role_profile": "",
            "is_custom": 1
        })
        role.insert()
        frappe.db.commit()
    
    # Create role if it doesn't exist
    if not frappe.db.exists("Role", "Aida Lead Intelligence Manager"):
        role = frappe.get_doc({
            "doctype": "Role",
            "role_name": "Aida Lead Intelligence Manager",
            "desk_access": 1,
            "restrict_to_domain": "",
            "two_factor_auth": 0,
            "role_profile": "",
            "is_custom": 1
        })
        role.insert()
        frappe.db.commit()

def create_initial_data():
    """Create initial sample data for demonstration"""
    # Create a sample lead generation history
    if not frappe.db.exists("Aida Lead Generation History", "DEMO-001"):
        history = frappe.get_doc({
            "doctype": "Aida Lead Generation History",
            "user_query": "Find 5 tech companies in San Francisco",
            "source": "gmaps",
            "criteria": '{"source": "gmaps", "search_terms": ["tech company"], "location": "San Francisco, USA", "max_leads": 5}',
            "leads_generated": 5,
            "status": "Completed",
            "success_rate": 100.0,
            "quality_score": 75.0
        })
        history.insert()
        frappe.db.commit()
        
        # Create sample leads
        sample_leads = [
            {
                "company_name": "TechCorp Solutions",
                "industry": "Technology",
                "email": "contact@techcorp.com",
                "phone": "+1-555-0123",
                "website": "https://techcorp.com",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "source": "google_maps"
            },
            {
                "company_name": "InnovateSoft",
                "industry": "Software Development",
                "email": "hello@innovatesoft.com",
                "phone": "+1-555-0124",
                "website": "https://innovatesoft.com",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "source": "google_maps"
            },
            {
                "company_name": "Digital Dynamics",
                "industry": "Digital Marketing",
                "email": "info@digitaldynamics.com",
                "phone": "+1-555-0125",
                "website": "https://digitaldynamics.com",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "source": "google_maps"
            }
        ]
        
        for i, lead_data in enumerate(sample_leads):
            lead = frappe.get_doc({
                "doctype": "Aida Generated Lead",
                "lead_generation_history": history.name,
                "company_name": lead_data["company_name"],
                "industry": lead_data["industry"],
                "email": lead_data["email"],
                "phone": lead_data["phone"],
                "website": lead_data["website"],
                "city": lead_data["city"],
                "state": lead_data["state"],
                "country": lead_data["country"],
                "source": lead_data["source"],
                "generated_at": now_datetime().isoformat()
            })
            lead.insert()
            
            # Create a sample score for the first lead
            if i == 0:
                score = frappe.get_doc({
                    "doctype": "Aida Lead Score",
                    "lead": lead.name,
                    "score": 85,
                    "status": "HOT",
                    "scoring_factors": '{"contact_completeness": {"score": 25, "details": "Complete contact information"}, "industry_relevance": {"score": 20, "details": "High-tech industry"}, "company_size_growth": {"score": 15, "details": "Medium company size"}, "geographic_targeting": {"score": 15, "details": "Target market location"}, "online_presence": {"score": 10, "details": "Strong online presence"}}',
                    "summary": "High-quality tech company with complete information",
                    "recommendations": '["Immediate follow-up", "Personalized outreach", "Research company for specific pain points"]',
                    "risk_factors": "None identified",
                    "scoring_method": "ai_gemini",
                    "scored_at": now_datetime().isoformat()
                })
                score.insert()
                
                # Update lead with score
                lead.lead_score = score.name
                lead.score = 85
                lead.status = "HOT"
                lead.save()
        
        frappe.db.commit()

def before_uninstall():
    """Cleanup tasks before app uninstallation"""
    try:
        # Remove custom roles
        roles_to_remove = ["Aida Lead Intelligence User", "Aida Lead Intelligence Manager"]
        for role_name in roles_to_remove:
            if frappe.db.exists("Role", role_name):
                frappe.delete_doc("Role", role_name)
        
        # Remove dashboard page
        if frappe.db.exists("Page", "aida-dashboard"):
            frappe.delete_doc("Page", "aida-dashboard")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error during Aida Lead Intelligence uninstallation: {str(e)}")

def after_migrate():
    """Tasks to run after app migration"""
    try:
        # Update any existing data if needed
        update_existing_data()
        
    except Exception as e:
        frappe.log_error(f"Error during Aida Lead Intelligence migration: {str(e)}")

def update_existing_data():
    """Update existing data after migration"""
    # This function can be used to update existing data
    # when the app schema changes
    pass