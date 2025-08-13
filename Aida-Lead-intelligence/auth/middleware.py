from functools import wraps
from flask import request, jsonify, session, g
from models.database import Database, UserManager, SessionManager
from typing import Optional, Dict, Any

# Initialize database components
db = Database()
user_manager = UserManager(db)
session_manager = SessionManager(db)

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session token in headers or session
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
        else:
            token = session.get('session_token')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        # Validate session
        user_id = session_manager.validate_session(token)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired session'
            }), 401
        
        # Store user info in Flask's g object for use in the route
        g.current_user_id = user_id
        g.session_token = token
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user information"""
    if hasattr(g, 'current_user_id'):
        return user_manager.get_user_by_id(g.current_user_id)
    return None

def login_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticate user and create session"""
    try:
        # Authenticate user
        user = user_manager.authenticate_user(username, password)
        if not user:
            return {
                'success': False,
                'message': 'Invalid username or password'
            }
        
        # Create session
        session_token = session_manager.create_session(user['id'])
        if not session_token:
            return {
                'success': False,
                'message': 'Failed to create session'
            }
        
        # Store in Flask session
        session['session_token'] = session_token
        session['user_id'] = user['id']
        
        return {
            'success': True,
            'message': 'Login successful',
            'user': user,
            'session_token': session_token
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Login failed: {str(e)}'
        }

def logout_user() -> Dict[str, Any]:
    """Logout user and invalidate session"""
    try:
        # Get session token
        token = session.get('session_token')
        if token:
            # Invalidate session in database
            session_manager.invalidate_session(token)
        
        # Clear Flask session
        session.clear()
        
        return {
            'success': True,
            'message': 'Logout successful'
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }

def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Register new user"""
    try:
        # Validate input
        if not username or not email or not password:
            return {
                'success': False,
                'message': 'All fields are required'
            }
        
        if len(password) < 6:
            return {
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }
        
        # Create user
        user_id = user_manager.create_user(username, email, password)
        if not user_id:
            return {
                'success': False,
                'message': 'Username or email already exists'
            }
        
        # Get user info
        user = user_manager.get_user_by_id(user_id)
        
        return {
            'success': True,
            'message': 'Registration successful',
            'user': user
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }

def cleanup_sessions():
    """Clean up expired sessions"""
    try:
        session_manager.cleanup_expired_sessions()
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")