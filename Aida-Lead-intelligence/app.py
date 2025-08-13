from flask import Flask, request, jsonify, make_response, session, Response, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import csv
import io
from datetime import datetime

# Import our custom modules
from services.lead_generator import LeadGenerator
from services.ai_agent import AIAgent
from services.erp_integration import ERPIntegration
from services.email_tracker import EmailTracker
from config.settings import get_config

# Import authentication and database modules
from auth.middleware import require_auth, get_current_user, login_user, logout_user, register_user, cleanup_sessions
from models.database import Database, UserManager, SessionManager, ConfigManager

# Import lead scoring service
from services.lead_scoring import LeadScoringService
lead_scoring_service = LeadScoringService()

# Load environment variables
load_dotenv()

# Get configuration based on environment
config_class = get_config()

app = Flask(__name__)
app.config.from_object(config_class)
CORS(app)

# Initialize configuration
config_class.init_app(app)

# Initialize database and managers
db = Database(app.config['DATABASE_PATH'])
user_manager = UserManager(db)
session_manager = SessionManager(db)
config_manager = ConfigManager(db)

# Initialize services
lead_generator = LeadGenerator()
ai_agent = AIAgent()
erp_integration = ERPIntegration()
email_tracker = EmailTracker(db)

# Health check route
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Web UI routes removed - API-only platform

# Authentication API routes
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """User login API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        result = login_user(username, password)
        
        if result['success']:
            response = jsonify({
                'success': True,
                'message': 'Login successful',
                'user': result['user'],
                'session_token': result['session_token']
            })
            response.set_cookie('token', result['session_token'], httponly=True, secure=False)  # Set secure=True in production
            return response
        else:
            return jsonify({'error': result['message']}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """User registration API"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        result = register_user(username, email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Registration successful'
            })
        else:
            return jsonify({'error': result['message']}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """User logout API"""
    try:
        logout_user()
        
        response = jsonify({'success': True, 'message': 'Logout successful'})
        response.set_cookie('token', '', expires=0)
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User profile API routes
@app.route('/api/user/profile', methods=['GET', 'PUT'])
@require_auth
def user_profile():
    """Get or update user profile"""
    try:
        user = get_current_user()
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'created_at': user['created_at']
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            
            if not username or not email:
                return jsonify({'error': 'Username and email required'}), 400
            
            success = user_manager.update_user(user['id'], username, email)
            
            if success:
                return jsonify({'success': True, 'message': 'Profile updated successfully'})
            else:
                return jsonify({'error': 'Failed to update profile'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Configuration API routes
@app.route('/api/config/erp', methods=['GET', 'POST'])
@require_auth
def erp_config():
    """Get or save ERP configuration"""
    try:
        user = get_current_user()
        
        if request.method == 'GET':
            config = config_manager.get_erpnext_config(user['id'])
            if config:
                # Map backend field names to frontend expected names
                mapped_config = {
                    'erp_url': config.get('url', ''),
                    'erp_username': config.get('username', ''),
                    'erp_password': '',  # Don't send password back for security
                    'erp_api_key': config.get('api_key', '')
                }
                return jsonify(mapped_config)
            else:
                return jsonify({})
        
        elif request.method == 'POST':
            data = request.get_json()
            # Map frontend field names to backend expected names
            mapped_data = {
                'url': data.get('erp_url'),
                'username': data.get('erp_username'),
                'password': data.get('erp_password'),
                'api_key': data.get('erp_api_key')  # Optional field
            }
            success = config_manager.save_erpnext_config(user['id'], mapped_data)
            
            if success:
                return jsonify({'success': True, 'message': 'ERP configuration saved'})
            else:
                return jsonify({'error': 'Failed to save ERP configuration'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/company', methods=['GET', 'POST'])
@require_auth
def company_config():
    """Get or save company configuration"""
    try:
        user = get_current_user()
        
        if request.method == 'GET':
            config = config_manager.get_company_config(user['id'])
            return jsonify(config or {})
        
        elif request.method == 'POST':
            data = request.get_json()
            success = config_manager.save_company_config(user['id'], data)
            
            if success:
                return jsonify({'success': True, 'message': 'Company configuration saved'})
            else:
                return jsonify({'error': 'Failed to save company configuration'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-leads', methods=['POST'])
@require_auth
def generate_leads():
    """Generate leads based on user query"""
    try:
        user = get_current_user()
        data = request.get_json()
        user_query = data.get('query', '')
        
        # Use AI agent to extract lead generation criteria
        criteria = ai_agent.extract_lead_criteria(user_query)
        
        # Generate leads using appropriate source
        leads = lead_generator.generate_leads(criteria)
        
        # Save lead generation record and get the ID
        lead_history_id = config_manager.save_lead_generation(
            user['id'],
            user_query,
            'ai_agent',
            len(leads),
            0
        )
        
        # Save individual leads to the leads table
        if lead_history_id and leads:
            config_manager.save_individual_leads(user['id'], lead_history_id, leads)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(leads)} leads successfully',
            'leads': leads,
            'criteria': criteria,
            'leads_count': len(leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-apollo-leads', methods=['POST'])
@require_auth
def generate_apollo_leads():
    """Generate leads from Apollo API"""
    try:
        user = get_current_user()
        data = request.get_json()
        url = data.get('url', '')
        page = data.get('page', 1)
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'Apollo URL is required'
            }), 400
        
        # Prepare criteria for Apollo lead generation
        criteria = {
            'source': 'apollo',
            'url': url,
            'page': page
        }
        
        # Generate leads using Apollo
        leads = lead_generator.generate_leads(criteria)
        
        # Save lead generation record and get the ID
        lead_history_id = config_manager.save_lead_generation(
            user['id'],
            f"Apollo URL: {url} (Page {page})",
            'apollo',
            len(leads),
            0
        )
        
        # Save individual leads to the leads table
        if lead_history_id and leads:
            config_manager.save_individual_leads(user['id'], lead_history_id, leads)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(leads)} Apollo leads successfully',
            'leads': leads,
            'criteria': criteria,
            'leads_count': len(leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/score', methods=['POST'])
@require_auth
def score_lead():
    """Score a single lead"""
    try:
        user = get_current_user()
        data = request.get_json()
        lead_id = data.get('lead_id')
        
        print(f"Scoring lead {lead_id} for user {user['id']}")
        
        if not lead_id:
            return jsonify({
                'success': False,
                'error': 'Lead ID is required'
            }), 400
        
        # Get the lead data
        lead = config_manager.get_lead_by_id(user['id'], lead_id)
        if not lead:
            print(f"Lead {lead_id} not found for user {user['id']}")
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        print(f"Found lead: {lead.get('name', 'Unknown')}")
        
        # Score the lead
        scoring_result = lead_scoring_service.score_lead(lead)
        
        print(f"Scoring result: {scoring_result.get('score', 'N/A')} - {scoring_result.get('status', 'N/A')}")
        
        # Save the score to database
        score_id = config_manager.save_lead_score(user['id'], lead_id, scoring_result)
        
        if score_id:
            print(f"Score saved with ID: {score_id}")
            return jsonify({
                'success': True,
                'message': 'Lead scored successfully',
                'scoring': scoring_result,
                'score_id': score_id
            })
        else:
            print("Failed to save score")
            return jsonify({
                'success': False,
                'error': 'Failed to save lead score'
            }), 500
    
    except Exception as e:
        print(f"Error scoring lead: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/batch-score', methods=['POST'])
@require_auth
def batch_score_leads():
    """Score multiple leads in batch"""
    try:
        user = get_current_user()
        data = request.get_json()
        lead_ids = data.get('lead_ids', [])
        
        if not lead_ids:
            return jsonify({
                'success': False,
                'error': 'Lead IDs are required'
            }), 400
        
        scored_leads = []
        for lead_id in lead_ids:
            try:
                # Get the lead data
                lead = config_manager.get_lead_by_id(user['id'], lead_id)
                if lead:
                    # Score the lead
                    scoring_result = lead_scoring_service.score_lead(lead)
                    
                    # Save the score to database
                    score_id = config_manager.save_lead_score(user['id'], lead_id, scoring_result)
                    
                    scored_leads.append({
                        'lead_id': lead_id,
                        'scoring': scoring_result,
                        'score_id': score_id
                    })
            except Exception as e:
                print(f"Error scoring lead {lead_id}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Scored {len(scored_leads)} leads successfully',
            'scored_leads': scored_leads
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/scored', methods=['GET'])
@require_auth
def get_scored_leads():
    """Get all scored leads for the user"""
    try:
        user = get_current_user()
        limit = request.args.get('limit', type=int)
        
        scored_leads = config_manager.get_user_lead_scores(user['id'], limit)
        
        return jsonify({
            'success': True,
            'scored_leads': scored_leads,
            'count': len(scored_leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/<int:lead_id>/score', methods=['GET'])
@require_auth
def get_lead_score(lead_id):
    """Get scoring data for a specific lead"""
    try:
        user = get_current_user()
        
        scoring_data = config_manager.get_lead_score(user['id'], lead_id)
        
        if scoring_data:
            return jsonify({
                'success': True,
                'scoring': scoring_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Lead score not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/scoring-summary', methods=['GET'])
@require_auth
def get_lead_scoring_summary():
    """Get lead scoring summary statistics"""
    try:
        user = get_current_user()
        
        summary = config_manager.get_lead_scoring_summary(user['id'])
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@require_auth
def settings():
    """Manage platform settings"""
    try:
        user = get_current_user()
        
        if request.method == 'GET':
            settings = config_manager.get_user_settings(user['id'])
            return jsonify(settings or {})
        
        elif request.method == 'POST':
            data = request.get_json()
            success = config_manager.save_user_settings(user['id'], data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Settings updated successfully'
                })
            else:
                return jsonify({'error': 'Failed to update settings'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/erp/test-connection', methods=['GET', 'POST'])
@require_auth
def test_connection():
    """Test ERPNext connection"""
    try:
        user = get_current_user()
        
        if request.method == 'POST':
            # Test with provided credentials
            data = request.get_json()
            # Map frontend field names to backend expected names
            mapped_data = {
                'url': data.get('erp_url'),
                'username': data.get('erp_username'),
                'password': data.get('erp_password'),
                'api_key': data.get('erp_api_key')  # Optional field
            }
            result = erp_integration.test_connection_with_config(mapped_data)
        else:
            # Test with saved user configuration
            erp_config = config_manager.get_erpnext_config(user['id'])
            if not erp_config:
                return jsonify({
                    'success': False,
                    'error': 'No ERP configuration found. Please configure your ERP settings first.'
                }), 400
            
            result = erp_integration.test_connection_with_config(erp_config)
        
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', 'Connection test completed'),
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/lead-sources', methods=['GET'])
@require_auth
def get_lead_sources():
    """Get available lead generation sources"""
    try:
        sources = lead_generator.get_available_sources()
        return jsonify(sources)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard and lead management API routes
@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        user = get_current_user()
        stats = config_manager.get_lead_stats(user['id'])
        
        # Check ERP connection status
        erp_config = config_manager.get_erpnext_config(user['id'])
        erp_status = 'Not Connected'
        if erp_config:
            try:
                test_result = erp_integration.test_connection_with_config(erp_config)
                erp_status = 'Connected' if test_result.get('success') else 'Connection Failed'
            except:
                erp_status = 'Connection Failed'
        
        stats['erp_status'] = erp_status
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads', methods=['GET'])
@require_auth
def get_leads():
    """Get user's leads"""
    try:
        user = get_current_user()
        leads = config_manager.get_user_leads(user['id'])
        return jsonify({
            'success': True,
            'leads': leads,
            'count': len(leads)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/recent', methods=['GET'])
@require_auth
def get_recent_leads():
    """Get recently generated leads (last generation session)"""
    try:
        user = get_current_user()
        recent_leads = config_manager.get_recent_leads(user['id'])
        
        return jsonify({
            'success': True,
            'leads': recent_leads,
            'count': len(recent_leads)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@require_auth
def delete_lead(lead_id):
    """Delete a lead"""
    try:
        user = get_current_user()
        success = config_manager.delete_lead(user['id'], lead_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Lead deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete lead'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/generate', methods=['POST'])
@require_auth
def generate_leads_api():
    """Generate leads API endpoint"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Build query from form data
        query_parts = []
        if data.get('industry'):
            query_parts.append(f"industry: {data['industry']}")
        if data.get('location'):
            query_parts.append(f"location: {data['location']}")
        if data.get('company_size'):
            query_parts.append(f"company size: {data['company_size']}")
        
        user_query = ', '.join(query_parts) if query_parts else 'general business leads'
        count = int(data.get('count', 10))
        
        # Use AI agent to extract lead generation criteria
        criteria = ai_agent.extract_lead_criteria(user_query)
        criteria['count'] = count
        
        # Generate leads using appropriate source
        leads = lead_generator.generate_leads(criteria)
        
        # Save lead generation record and get the ID
        lead_history_id = config_manager.save_lead_generation(
            user['id'],
            user_query,
            'api_generate',
            len(leads),
            0
        )
        
        # Save individual leads to the leads table
        if lead_history_id and leads:
            config_manager.save_individual_leads(user['id'], lead_history_id, leads)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(leads)} leads successfully',
            'count': len(leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leads/export', methods=['GET'])
@require_auth
def export_leads():
    """Export leads to CSV"""
    try:
        user = get_current_user()
        leads = config_manager.get_user_leads(user['id'])
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Query', 'Source', 'Generated Count', 'Synced Count', 'Status', 'Date'])
        
        # Write data
        for lead in leads:
            writer.writerow([
                lead.get('id', ''),
                lead.get('query', ''),
                lead.get('source', ''),
                lead.get('generated_count', 0),
                lead.get('synced_count', 0),
                lead.get('status', ''),
                lead.get('created_at', '')
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=leads_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/erp/sync', methods=['POST'])
@require_auth
def sync_with_erp():
    """Sync leads with ERP"""
    try:
        user = get_current_user()
        
        # Get ERP configuration
        erp_config = config_manager.get_erpnext_config(user['id'])
        if not erp_config:
            return jsonify({
                'success': False,
                'error': 'No ERP configuration found'
            }), 400
        
        # Get recent leads to sync
        leads = config_manager.get_user_leads(user['id'], limit=50)
        
        # Sync with ERP (placeholder implementation)
        synced_count = 0
        for lead in leads:
            # Here you would implement actual ERP sync logic
            synced_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Synced {synced_count} leads with ERP',
            'synced_count': synced_count
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/add-to-crm', methods=['POST'])
@require_auth
def add_leads_to_crm():
    """Add selected leads to ERPNext CRM"""
    try:
        user = get_current_user()
        data = request.get_json()
        leads = data.get('leads', [])
        
        if not leads:
            return jsonify({
                'success': False,
                'message': 'No leads provided'
            }), 400
        
        # Get user's ERP configuration
        erp_config = config_manager.get_erpnext_config(user['id'])
        if not erp_config:
            return jsonify({
                'success': False,
                'message': 'ERP configuration not found'
            }), 400
        
        # Create leads in ERPNext
        erp_results = []
        successful_count = 0
        
        for lead in leads:
            erp_result = erp_integration.create_lead_with_config(lead, erp_config)
            erp_results.append(erp_result)
            if erp_result.get('success'):
                successful_count += 1
                # Save lead to database
                config_manager.save_lead_generation(
                    user['id'],
                    f"CRM Lead: {lead.get('name', 'Unknown')}",
                    'crm_bulk',
                    1,
                    1
                )
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {successful_count}/{len(leads)} leads to CRM',
            'results': erp_results,
            'successful_count': successful_count,
            'total_count': len(leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to add leads to CRM: {str(e)}'
        }), 500

@app.route('/api/add-single-to-crm', methods=['POST'])
@require_auth
def add_single_lead_to_crm():
    """Add a single lead to ERPNext CRM"""
    try:
        user = get_current_user()
        data = request.get_json()
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return jsonify({
                'success': False,
                'message': 'No lead ID provided'
            }), 400
        
        # Get the lead data from database
        lead = config_manager.get_lead_by_id(user['id'], lead_id)
        if not lead:
            return jsonify({
                'success': False,
                'message': 'Lead not found'
            }), 404
        
        # Parse the lead data
        lead_data = json.loads(lead['data']) if isinstance(lead['data'], str) else lead['data']
        
        # Get user's ERP configuration
        erp_config = config_manager.get_erpnext_config(user['id'])
        if not erp_config:
            return jsonify({
                'success': False,
                'message': 'ERP configuration not found'
            }), 400
        
        # Create lead in ERPNext
        erp_result = erp_integration.create_lead_with_config(lead_data, erp_config)
        
        if erp_result.get('success'):
            # Mark lead as added to CRM in database
            config_manager.mark_individual_lead_synced(lead_id)
        
        return jsonify({
            'success': erp_result.get('success', False),
            'message': erp_result.get('message', 'Unknown error'),
            'lead_name': erp_result.get('lead_name', ''),
            'result': erp_result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to add lead to CRM: {str(e)}'
        }), 500

# Outreach API routes
@app.route('/api/outreach/crm-leads', methods=['GET'])
@require_auth
def get_crm_leads():
    """Get leads from ERPNext CRM"""
    try:
        user = get_current_user()
        
        # Get user's ERP configuration
        erp_config = config_manager.get_erpnext_config(user['id'])
        if not erp_config:
            return jsonify({
                'success': False,
                'message': 'ERP configuration not found'
            }), 400
        
        # Fetch leads from ERPNext
        leads = erp_integration.get_existing_leads_with_config(erp_config)
        
        return jsonify({
            'success': True,
            'leads': leads,
            'count': len(leads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch CRM leads: {str(e)}'
        }), 500

@app.route('/api/outreach/import-crm-leads', methods=['POST'])
@require_auth
def import_crm_leads():
    """Import leads from ERPNext CRM to local database"""
    try:
        user = get_current_user()
        data = request.get_json()
        crm_leads = data.get('leads', [])
        
        if not crm_leads:
            return jsonify({
                'success': False,
                'message': 'No leads provided for import'
            }), 400
        
        # Import leads to local database
        imported_leads = []
        imported_count = 0
        
        for crm_lead in crm_leads:
            # Convert CRM lead format to local format
            lead_data = {
                'company_name': crm_lead.get('company_name', ''),
                'name': crm_lead.get('lead_name', ''),
                'email': crm_lead.get('email_id', ''),
                'phone': crm_lead.get('phone', ''),
                'address': crm_lead.get('address_line1', ''),
                'city': crm_lead.get('city', ''),
                'state': crm_lead.get('state', ''),
                'country': crm_lead.get('country', ''),
                'website': crm_lead.get('website', ''),
                'category': crm_lead.get('source', 'CRM Import'),  # Use 'CRM Import' as default if source not available
                'status': crm_lead.get('status', ''),
                'source': 'crm_import'
            }
            
            # Save to local database
            lead_id = config_manager.save_imported_lead(user['id'], lead_data)
            if lead_id:
                imported_count += 1
                imported_leads.append({
                    'id': lead_id,
                    'name': lead_data['name'],
                    'email': lead_data['email'],
                    'phone': lead_data['phone'],
                    'address': lead_data['address'],
                    'category': lead_data['category']
                })
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} leads from CRM',
            'imported_count': imported_count,
            'imported_leads': imported_leads
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to import CRM leads: {str(e)}'
        }), 500

# Email Template Management API routes
@app.route('/api/email/templates', methods=['GET'])
@require_auth
def get_email_templates():
    """Get all email templates for the current user"""
    try:
        user = get_current_user()
        templates = config_manager.get_email_templates(user['id'])
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email templates: {str(e)}'
        }), 500

@app.route('/api/email/templates', methods=['POST'])
@require_auth
def create_email_template():
    """Create a new email template"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': 'Template name and content are required'
            }), 400
        
        # Save template
        template_id = config_manager.save_email_template(user['id'], data)
        
        if template_id:
            return jsonify({
                'success': True,
                'message': 'Email template created successfully',
                'template_id': template_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create email template'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create email template: {str(e)}'
        }), 500

@app.route('/api/email/templates/<int:template_id>', methods=['GET'])
@require_auth
def get_email_template(template_id):
    """Get a specific email template"""
    try:
        user = get_current_user()
        template = config_manager.get_email_template_by_id(user['id'], template_id)
        
        if template:
            return jsonify({
                'success': True,
                'template': template
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email template not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email template: {str(e)}'
        }), 500

@app.route('/api/email/templates/<int:template_id>', methods=['PUT'])
@require_auth
def update_email_template(template_id):
    """Update an email template"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': 'Template name and content are required'
            }), 400
        
        # Update template
        success = config_manager.update_email_template(user['id'], template_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email template updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update email template'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to update email template: {str(e)}'
        }), 500

@app.route('/api/email/templates/<int:template_id>', methods=['DELETE'])
@require_auth
def delete_email_template(template_id):
    """Delete an email template"""
    try:
        user = get_current_user()
        success = config_manager.delete_email_template(user['id'], template_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email template deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete email template'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to delete email template: {str(e)}'
        }), 500

@app.route('/api/email/templates/<int:template_id>/test', methods=['POST'])
@require_auth
def test_email_template(template_id):
    """Test an email template with sample data"""
    try:
        user = get_current_user()
        data = request.get_json()
        test_data = data.get('test_data', {})
        
        # Get template
        template = config_manager.get_email_template_by_id(user['id'], template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': 'Email template not found'
            }), 404
        
        # Process template with test data
        subject = template['subject'] or ''
        content = template['content'] or ''
        
        # Replace variables in subject and content
        for key, value in test_data.items():
            placeholder = f'{{{{{key}}}}}'
            subject = subject.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))
        
        return jsonify({
            'success': True,
            'processed_template': {
                'subject': subject,
                'content': content,
                'original_template': template
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to test email template: {str(e)}'
        }), 500

# Email Tracking API routes
@app.route('/api/email/track/open/<tracking_id>', methods=['GET'])
def track_email_open(tracking_id):
    """Track email open via tracking pixel"""
    try:
        # Debug logging
        print(f"🔍 Tracking email open: {tracking_id}")
        print(f"   IP: {request.remote_addr}")
        print(f"   User-Agent: {request.headers.get('User-Agent', '')}")
        print(f"   Referer: {request.headers.get('Referer', '')}")
        
        # Get IP address and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Track the open event
        success = email_tracker.track_email_event(
            tracking_id=tracking_id,
            event_type='opened',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            print(f"✅ Successfully tracked open for: {tracking_id}")
            # Return a 1x1 transparent GIF
            gif_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
            return Response(gif_data, mimetype='image/gif')
        else:
            print(f"❌ Failed to track open for: {tracking_id}")
            return Response('', status=404)
    
    except Exception as e:
        print(f"❌ Error tracking email open: {e}")
        return Response('', status=500)

@app.route('/api/email/track/click/<tracking_id>', methods=['GET'])
def track_email_click(tracking_id):
    """Track email link click"""
    try:
        # Debug logging
        print(f"🔍 Tracking email click: {tracking_id}")
        print(f"   IP: {request.remote_addr}")
        print(f"   User-Agent: {request.headers.get('User-Agent', '')}")
        print(f"   Referer: {request.headers.get('Referer', '')}")
        
        # Get redirect URL
        redirect_url = request.args.get('url', '')
        print(f"   Redirect URL: {redirect_url}")
        
        # Get IP address and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Track the click event
        success = email_tracker.track_email_event(
            tracking_id=tracking_id,
            event_type='clicked',
            ip_address=ip_address,
            user_agent=user_agent,
            event_data={'redirect_url': redirect_url}
        )
        
        if success and redirect_url:
            print(f"✅ Successfully tracked click for: {tracking_id}")
            # Redirect to the original URL
            return redirect(redirect_url)
        else:
            print(f"❌ Failed to track click for: {tracking_id}")
            return Response('Invalid tracking ID', status=404)
    
    except Exception as e:
        print(f"❌ Error tracking email click: {e}")
        return Response('Error tracking click', status=500)

@app.route('/api/email/track/unsubscribe/<tracking_id>', methods=['GET'])
def track_email_unsubscribe(tracking_id):
    """Track email unsubscribe"""
    try:
        # Get IP address and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Track the unsubscribe event
        success = email_tracker.track_email_event(
            tracking_id=tracking_id,
            event_type='unsubscribed',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully unsubscribed'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to unsubscribe'
            }), 400
    
    except Exception as e:
        print(f"Error tracking unsubscribe: {e}")
        return jsonify({
            'success': False,
            'message': 'Error processing unsubscribe'
        }), 500

@app.route('/api/email/track', methods=['POST'])
@require_auth
def track_email():
    """Track an email event (open, click, bounce, etc.)"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        tracking_id = data.get('tracking_id')
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not all([tracking_id, event_type]):
            return jsonify({
                'success': False,
                'message': 'Tracking ID and event type are required'
            }), 400
        
        # Track the event
        success = email_tracker.track_email_event(
            tracking_id=tracking_id,
            event_type=event_type,
            event_data=event_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email event tracked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to track email event'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to track email event: {str(e)}'
        }), 500

@app.route('/api/email/track/<int:event_id>', methods=['GET'])
@require_auth
def get_email_event(event_id):
    """Get a specific email event by ID"""
    try:
        user = get_current_user()
        event = email_tracker.get_event_by_id(user['id'], event_id)
        
        if event:
            return jsonify({
                'success': True,
                'event': event
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email event not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email event: {str(e)}'
        }), 500

@app.route('/api/email/track/email/<int:email_id>', methods=['GET'])
@require_auth
def get_email_events_by_email(email_id):
    """Get all events for a specific email ID"""
    try:
        user = get_current_user()
        events = email_tracker.get_events_by_email_id(user['id'], email_id)
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email events: {str(e)}'
        }), 500

@app.route('/api/email/track/campaigns', methods=['GET'])
@require_auth
def get_campaigns():
    """Get all campaigns for the current user"""
    try:
        user = get_current_user()
        campaigns = email_tracker.get_campaigns(user['id'])
        
        return jsonify({
            'success': True,
            'campaigns': campaigns,
            'count': len(campaigns)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch campaigns: {str(e)}'
        }), 500

@app.route('/api/email/track/campaigns', methods=['POST'])
@require_auth
def create_campaign():
    """Create a new campaign"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Campaign name is required'
            }), 400
        
        campaign_id = email_tracker.save_campaign(user['id'], data)
        
        if campaign_id:
            return jsonify({
                'success': True,
                'message': 'Campaign created successfully',
                'campaign_id': campaign_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create campaign'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create campaign: {str(e)}'
        }), 500

@app.route('/api/email/track/campaigns/<int:campaign_id>', methods=['GET'])
@require_auth
def get_campaign(campaign_id):
    """Get a specific campaign by ID"""
    try:
        user = get_current_user()
        campaign = email_tracker.get_campaign_by_id(user['id'], campaign_id)
        
        if campaign:
            return jsonify({
                'success': True,
                'campaign': campaign
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Campaign not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch campaign: {str(e)}'
        }), 500

@app.route('/api/email/track/campaigns/<int:campaign_id>', methods=['PUT'])
@require_auth
def update_campaign(campaign_id):
    """Update a campaign"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Campaign name is required'
            }), 400
        
        success = email_tracker.update_campaign(user['id'], campaign_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Campaign updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update campaign'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to update campaign: {str(e)}'
        }), 500

@app.route('/api/email/track/campaigns/<int:campaign_id>', methods=['DELETE'])
@require_auth
def delete_campaign(campaign_id):
    """Delete a campaign"""
    try:
        user = get_current_user()
        success = email_tracker.delete_campaign(user['id'], campaign_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Campaign deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete campaign'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to delete campaign: {str(e)}'
        }), 500

@app.route('/api/email/track/sequences', methods=['GET'])
@require_auth
def get_sequences():
    """Get all sequences for the current user"""
    try:
        user = get_current_user()
        sequences = email_tracker.get_sequences(user['id'])
        
        return jsonify({
            'success': True,
            'sequences': sequences,
            'count': len(sequences)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch sequences: {str(e)}'
        }), 500

@app.route('/api/email/track/sequences', methods=['POST'])
@require_auth
def create_sequence():
    """Create a new sequence"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Sequence name is required'
            }), 400
        
        sequence_id = email_tracker.save_sequence(user['id'], data)
        
        if sequence_id:
            return jsonify({
                'success': True,
                'message': 'Sequence created successfully',
                'sequence_id': sequence_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create sequence'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create sequence: {str(e)}'
        }), 500

@app.route('/api/email/track/sequences/<int:sequence_id>', methods=['GET'])
@require_auth
def get_sequence(sequence_id):
    """Get a specific sequence by ID"""
    try:
        user = get_current_user()
        sequence = email_tracker.get_sequence_by_id(user['id'], sequence_id)
        
        if sequence:
            return jsonify({
                'success': True,
                'sequence': sequence
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Sequence not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch sequence: {str(e)}'
        }), 500

@app.route('/api/email/track/sequences/<int:sequence_id>', methods=['PUT'])
@require_auth
def update_sequence(sequence_id):
    """Update a sequence"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Sequence name is required'
            }), 400
        
        success = email_tracker.update_sequence(user['id'], sequence_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sequence updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update sequence'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to update sequence: {str(e)}'
        }), 500

@app.route('/api/email/track/sequences/<int:sequence_id>', methods=['DELETE'])
@require_auth
def delete_sequence(sequence_id):
    """Delete a sequence"""
    try:
        user = get_current_user()
        success = email_tracker.delete_sequence(user['id'], sequence_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sequence deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete sequence'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to delete sequence: {str(e)}'
        }), 500

@app.route('/api/email/track/analytics/campaigns', methods=['GET'])
@require_auth
def get_campaign_analytics():
    """Get analytics for campaigns"""
    try:
        user = get_current_user()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        campaign_name = request.args.get('campaign_name')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Start date and end date are required for analytics'
            }), 400
        
        analytics = email_tracker.get_campaign_analytics(user['id'], start_date, end_date, campaign_name)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to get campaign analytics: {str(e)}'
        }), 500

@app.route('/api/email/track/analytics/sequences', methods=['GET'])
@require_auth
def get_sequence_analytics():
    """Get analytics for sequences"""
    try:
        user = get_current_user()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sequence_name = request.args.get('sequence_name')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Start date and end date are required for analytics'
            }), 400
        
        analytics = email_tracker.get_sequence_analytics(user['id'], start_date, end_date, sequence_name)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to get sequence analytics: {str(e)}'
        }), 500

# Email sending endpoints with tracking
@app.route('/api/email/send', methods=['POST'])
@require_auth
def send_tracked_email():
    """Send an email with tracking enabled"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        lead_id = data.get('lead_id')
        template_id = data.get('template_id')
        email_address = data.get('email_address')
        subject = data.get('subject')
        content = data.get('content')
        campaign_id = data.get('campaign_id')
        sequence_id = data.get('sequence_id')
        
        if not all([lead_id, template_id, email_address, subject, content]):
            return jsonify({
                'success': False,
                'message': 'Lead ID, template ID, email address, subject, and content are required'
            }), 400
        
        # Send email with tracking
        tracking_id = email_tracker.create_tracking_email(
            user_id=user['id'],
            lead_id=lead_id,
            template_id=template_id,
            email_address=email_address,
            subject=subject,
            content=content,
            campaign_id=campaign_id,
            sequence_id=sequence_id
        )
        
        if tracking_id:
            return jsonify({
                'success': True,
                'message': 'Email sent successfully with tracking',
                'tracking_id': tracking_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send email'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to send email: {str(e)}'
        }), 500

@app.route('/api/email/campaigns', methods=['GET'])
@require_auth
def get_email_campaigns():
    """Get all email campaigns for the current user"""
    try:
        user = get_current_user()
        campaigns = config_manager.get_email_campaigns(user['id'])
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch campaigns: {str(e)}'
        }), 500

@app.route('/api/email/campaigns', methods=['POST'])
@require_auth
def create_email_campaign():
    """Create a new email campaign"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Campaign name is required'
            }), 400
        
        campaign_id = config_manager.save_email_campaign(user['id'], data)
        
        if campaign_id:
            return jsonify({
                'success': True,
                'message': 'Campaign created successfully',
                'campaign_id': campaign_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create campaign'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create campaign: {str(e)}'
        }), 500

@app.route('/api/email/sequences', methods=['GET'])
@require_auth
def get_email_sequences():
    """Get all email sequences for the current user"""
    try:
        user = get_current_user()
        sequences = config_manager.get_email_sequences(user['id'])
        
        return jsonify({
            'success': True,
            'sequences': sequences
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch sequences: {str(e)}'
        }), 500

@app.route('/api/email/sequences', methods=['POST'])
@require_auth
def create_email_sequence():
    """Create a new email sequence"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Sequence name is required'
            }), 400
        
        sequence_id = config_manager.save_email_sequence(user['id'], data)
        
        if sequence_id:
            return jsonify({
                'success': True,
                'message': 'Sequence created successfully',
                'sequence_id': sequence_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create sequence'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create sequence: {str(e)}'
        }), 500

@app.route('/api/email/sequences/<int:sequence_id>/start', methods=['POST'])
@require_auth
def start_email_sequence(sequence_id):
    """Start an email sequence for a lead"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        lead_id = data.get('lead_id')
        if not lead_id:
            return jsonify({
                'success': False,
                'message': 'Lead ID is required'
            }), 400
        
        # Create sequence instance
        instance_id = config_manager.create_sequence_instance(user['id'], sequence_id, lead_id)
        
        if instance_id:
            return jsonify({
                'success': True,
                'message': 'Sequence started successfully',
                'instance_id': instance_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start sequence'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to start sequence: {str(e)}'
        }), 500

@app.route('/api/email/analytics', methods=['GET'])
@require_auth
def get_email_analytics():
    """Get email analytics for the current user"""
    try:
        user = get_current_user()
        days = request.args.get('days', 30, type=int)
        
        analytics = email_tracker.get_email_analytics(user['id'], days)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to get analytics: {str(e)}'
        }), 500

@app.route('/api/email/tracking/<tracking_id>', methods=['GET'])
@require_auth
def get_tracking_details(tracking_id):
    """Get detailed tracking information"""
    try:
        user = get_current_user()
        details = email_tracker.get_tracking_details(tracking_id)
        
        if details:
            return jsonify({
                'success': True,
                'details': details
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Tracking details not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to get tracking details: {str(e)}'
        }), 500

# Email server configuration endpoints
@app.route('/api/email/servers', methods=['GET'])
@require_auth
def get_email_servers():
    """Get all email server configurations for the current user"""
    try:
        user = get_current_user()
        configs = config_manager.get_email_server_configs(user['id'])
        
        return jsonify({
            'success': True,
            'configs': configs
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email servers: {str(e)}'
        }), 500

@app.route('/api/email/servers', methods=['POST'])
@require_auth
def create_email_server():
    """Create a new email server configuration"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        required_fields = ['name', 'smtp_server', 'smtp_port', 'sender_email', 'sender_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        config_id = config_manager.save_email_server_config(user['id'], data)
        
        if config_id:
            return jsonify({
                'success': True,
                'message': 'Email server configuration created successfully',
                'config_id': config_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create email server configuration'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to create email server configuration: {str(e)}'
        }), 500

@app.route('/api/email/servers/<int:config_id>', methods=['GET'])
@require_auth
def get_email_server(config_id):
    """Get a specific email server configuration"""
    try:
        user = get_current_user()
        config = config_manager.get_email_server_config_by_id(user['id'], config_id)
        
        if config:
            # Don't return the password for security
            config.pop('sender_password', None)
            return jsonify({
                'success': True,
                'config': config
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email server configuration not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch email server configuration: {str(e)}'
        }), 500

@app.route('/api/email/servers/<int:config_id>', methods=['PUT'])
@require_auth
def update_email_server(config_id):
    """Update an email server configuration"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        required_fields = ['name', 'smtp_server', 'smtp_port', 'sender_email', 'sender_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        success = config_manager.update_email_server_config(user['id'], config_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email server configuration updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update email server configuration'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to update email server configuration: {str(e)}'
        }), 500

@app.route('/api/email/servers/<int:config_id>', methods=['DELETE'])
@require_auth
def delete_email_server(config_id):
    """Delete an email server configuration"""
    try:
        user = get_current_user()
        success = config_manager.delete_email_server_config(user['id'], config_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email server configuration deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete email server configuration'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to delete email server configuration: {str(e)}'
        }), 500

@app.route('/api/email/servers/<int:config_id>/test-connection', methods=['POST'])
@require_auth
def test_email_connection(config_id):
    """Test email server connection"""
    try:
        user = get_current_user()
        result = email_tracker.test_email_connection(user['id'], config_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to test email connection: {str(e)}'
        }), 500

@app.route('/api/email/servers/<int:config_id>/test-email', methods=['POST'])
@require_auth
def send_test_email(config_id):
    """Send a test email with tracking"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        to_email = data.get('to_email')
        if not to_email:
            return jsonify({
                'success': False,
                'message': 'Recipient email address is required'
            }), 400
        
        subject = data.get('subject')
        content = data.get('content')
        
        result = email_tracker.send_test_email(
            user_id=user['id'],
            to_email=to_email,
            config_id=config_id,
            subject=subject,
            content=content
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to send test email: {str(e)}'
        }), 500

@app.route('/api/email/servers/active', methods=['GET'])
@require_auth
def get_active_email_server():
    """Get the active email server configuration"""
    try:
        user = get_current_user()
        config = config_manager.get_active_email_server_config(user['id'])
        
        if config:
            # Don't return the password for security
            config.pop('sender_password', None)
            return jsonify({
                'success': True,
                'config': config
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No active email server configuration found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to fetch active email server configuration: {str(e)}'
        }), 500

# Cleanup sessions on startup
cleanup_sessions()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)