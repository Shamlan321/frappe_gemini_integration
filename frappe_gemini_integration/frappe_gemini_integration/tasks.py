import frappe
from frappe.utils import now_datetime
from .services import LeadScoringService, LeadGenerator
import json

def daily_lead_scoring():
    """Daily task to score unscored leads"""
    try:
        frappe.logger().info("Starting daily lead scoring task")
        
        # Get unscored leads
        unscored_leads = frappe.get_list(
            "Aida Generated Lead",
            filters={"lead_score": ["is", "null"]},
            fields=["name", "company_name"],
            limit_page_length=100
        )
        
        if not unscored_leads:
            frappe.logger().info("No unscored leads found for daily scoring")
            return
        
        # Initialize scoring service
        scoring_service = LeadScoringService()
        
        # Score leads in batches
        batch_size = 10
        total_scored = 0
        
        for i in range(0, len(unscored_leads), batch_size):
            batch = unscored_leads[i:i + batch_size]
            
            for lead in batch:
                try:
                    # Get full lead data
                    lead_doc = frappe.get_doc("Aida Generated Lead", lead.name)
                    lead_data = lead_doc.as_dict()
                    
                    # Score the lead
                    scoring_result = scoring_service.score_lead(lead_data)
                    
                    # Save the score
                    score_doc = frappe.get_doc({
                        'doctype': 'Aida Lead Score',
                        'lead': lead.name,
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
                    
                    total_scored += 1
                    frappe.logger().info(f"Scored lead: {lead.company_name}")
                    
                except Exception as e:
                    frappe.logger().error(f"Error scoring lead {lead.name}: {str(e)}")
                    continue
            
            # Commit batch to avoid long transactions
            frappe.db.commit()
        
        frappe.logger().info(f"Daily lead scoring completed. Scored {total_scored} leads.")
        
    except Exception as e:
        frappe.logger().error(f"Error in daily lead scoring task: {str(e)}")

def hourly_lead_generation():
    """Hourly task to check for scheduled lead generation"""
    try:
        frappe.logger().info("Starting hourly lead generation task")
        
        # Check for any pending lead generation requests
        # This could be expanded to handle scheduled lead generation
        # For now, just log the task execution
        
        # Get recent lead generation statistics
        recent_generation = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(leads_generated) as total_leads,
                AVG(leads_generated) as avg_leads_per_session
            FROM `tabAida Lead Generation History`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, as_dict=True)
        
        if recent_generation and recent_generation[0]:
            stats = recent_generation[0]
            frappe.logger().info(f"Last 24 hours: {stats.total_sessions} sessions, {stats.total_leads} leads generated")
        
        frappe.logger().info("Hourly lead generation task completed")
        
    except Exception as e:
        frappe.logger().error(f"Error in hourly lead generation task: {str(e)}")

def cleanup_old_data():
    """Clean up old data to maintain database performance"""
    try:
        frappe.logger().info("Starting data cleanup task")
        
        # Clean up old lead generation history (older than 90 days)
        old_history = frappe.db.sql("""
            SELECT name FROM `tabAida Lead Generation History`
            WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)
        """)
        
        if old_history:
            for record in old_history:
                try:
                    frappe.delete_doc("Aida Lead Generation History", record[0])
                except:
                    continue
            
            frappe.logger().info(f"Cleaned up {len(old_history)} old lead generation history records")
        
        # Clean up old lead scores (older than 180 days)
        old_scores = frappe.db.sql("""
            SELECT name FROM `tabAida Lead Score`
            WHERE creation < DATE_SUB(NOW(), INTERVAL 180 DAY)
        """)
        
        if old_scores:
            for record in old_scores:
                try:
                    frappe.delete_doc("Aida Lead Score", record[0])
                except:
                    continue
            
            frappe.logger().info(f"Cleaned up {len(old_scores)} old lead score records")
        
        frappe.db.commit()
        frappe.logger().info("Data cleanup task completed")
        
    except Exception as e:
        frappe.logger().error(f"Error in data cleanup task: {str(e)}")

def sync_leads_to_erp():
    """Sync scored leads to ERP system"""
    try:
        frappe.logger().info("Starting ERP sync task")
        
        # Get leads that are scored but not synced to ERP
        unsynced_leads = frappe.get_list(
            "Aida Generated Lead",
            filters={
                "lead_score": ["is", "not null"],
                "synced_to_erp": 0
            },
            fields=["name", "company_name", "score", "status"],
            limit_page_length=50
        )
        
        if not unsynced_leads:
            frappe.logger().info("No leads to sync to ERP")
            return
        
        # Import ERP integration service
        from .services import ERPIntegration
        erp_integration = ERPIntegration()
        
        total_synced = 0
        total_failed = 0
        
        for lead in unsynced_leads:
            try:
                # Get full lead data
                lead_doc = frappe.get_doc("Aida Generated Lead", lead.name)
                lead_data = lead_doc.as_dict()
                
                # Sync to ERP
                result = erp_integration.create_lead_in_erp(lead_data)
                
                if result.get('success'):
                    # Update lead with ERP ID
                    lead_doc.erp_lead_id = result.get('erp_lead_id')
                    lead_doc.synced_to_erp = True
                    lead_doc.synced_at = now_datetime()
                    lead_doc.save()
                    
                    total_synced += 1
                    frappe.logger().info(f"Synced lead to ERP: {lead.company_name}")
                else:
                    total_failed += 1
                    frappe.logger().warning(f"Failed to sync lead {lead.company_name}: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                total_failed += 1
                frappe.logger().error(f"Error syncing lead {lead.name}: {str(e)}")
                continue
        
        frappe.db.commit()
        frappe.logger().info(f"ERP sync completed. Synced: {total_synced}, Failed: {total_failed}")
        
    except Exception as e:
        frappe.logger().error(f"Error in ERP sync task: {str(e)}")

def update_lead_statistics():
    """Update lead statistics and metrics"""
    try:
        frappe.logger().info("Starting lead statistics update task")
        
        # Update lead generation history with performance metrics
        history_records = frappe.get_list(
            "Aida Lead Generation History",
            filters={"status": "Completed"},
            fields=["name", "leads_generated"]
        )
        
        for record in history_records:
            try:
                # Calculate success rate and quality score
                generated_leads = frappe.get_list(
                    "Aida Generated Lead",
                    filters={"lead_generation_history": record.name},
                    fields=["name", "score"]
                )
                
                if generated_leads:
                    # Calculate success rate (leads with scores)
                    scored_leads = [lead for lead in generated_leads if lead.score is not None]
                    success_rate = (len(scored_leads) / len(generated_leads)) * 100 if generated_leads else 0
                    
                    # Calculate average quality score
                    total_score = sum(lead.score for lead in scored_leads if lead.score is not None)
                    avg_score = total_score / len(scored_leads) if scored_leads else 0
                    
                    # Update history record
                    history_doc = frappe.get_doc("Aida Lead Generation History", record.name)
                    history_doc.success_rate = success_rate
                    history_doc.quality_score = avg_score
                    history_doc.save()
                
            except Exception as e:
                frappe.logger().error(f"Error updating statistics for {record.name}: {str(e)}")
                continue
        
        frappe.db.commit()
        frappe.logger().info("Lead statistics update task completed")
        
    except Exception as e:
        frappe.logger().error(f"Error in lead statistics update task: {str(e)}")