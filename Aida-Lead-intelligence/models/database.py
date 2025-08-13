import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
import base64

class Database:
    """SQLite database manager for multi-tenant platform"""
    
    def __init__(self, db_path: str = 'platform.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables and perform migrations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Company configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT,
                industry TEXT,
                website TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # ERPNext configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS erpnext_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                username TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                encryption_key TEXT NOT NULL,
                api_key_encrypted TEXT,
                api_key_encryption_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                encryption_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Lead history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT,
                source TEXT,
                leads_generated INTEGER DEFAULT 0,
                leads_synced INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Individual leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lead_history_id INTEGER,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                rating REAL,
                category TEXT,
                data TEXT,
                is_synced BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (lead_history_id) REFERENCES lead_history (id)
            )
        ''')
        
        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                settings TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Lead enrichment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_enrichment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                enrichment_type TEXT,
                enrichment_data TEXT,
                enrichment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Lead scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                status TEXT NOT NULL,
                factors TEXT,
                recommendations TEXT,
                confidence TEXT,
                reasoning TEXT,
                scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                variables TEXT,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email sequences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                steps JSON NOT NULL,
                triggers JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (campaign_id) REFERENCES email_campaigns (id)
            )
        ''')
        
        # Email tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                sequence_id INTEGER,
                lead_id INTEGER,
                email_address TEXT NOT NULL,
                subject TEXT,
                template_id INTEGER,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                replied_at TIMESTAMP,
                bounced_at TIMESTAMP,
                unsubscribed_at TIMESTAMP,
                spam_reported_at TIMESTAMP,
                tracking_id TEXT UNIQUE,
                open_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (campaign_id) REFERENCES email_campaigns (id),
                FOREIGN KEY (sequence_id) REFERENCES email_sequences (id),
                FOREIGN KEY (lead_id) REFERENCES leads (id),
                FOREIGN KEY (template_id) REFERENCES email_templates (id)
            )
        ''')
        
        # Email tracking events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data JSON,
                ip_address TEXT,
                user_agent TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tracking_id) REFERENCES email_tracking (id)
            )
        ''')
        
        # Email sequence instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_sequence_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sequence_id INTEGER NOT NULL,
                lead_id INTEGER NOT NULL,
                current_step INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                paused_at TIMESTAMP,
                resumed_at TIMESTAMP,
                next_step_due TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (sequence_id) REFERENCES email_sequences (id),
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        # Email automation rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_conditions JSON,
                action_type TEXT NOT NULL,
                action_data JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email server configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_server_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                smtp_server TEXT NOT NULL,
                smtp_port INTEGER NOT NULL,
                sender_email TEXT NOT NULL,
                sender_password TEXT NOT NULL,
                sender_name TEXT,
                use_ssl BOOLEAN DEFAULT 0,
                use_tls BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Migration: Add missing columns to erpnext_configs if not exist
        cursor.execute("PRAGMA table_info(erpnext_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Handle the server_url vs url column issue
        if 'server_url' in columns and 'url' not in columns:
            # If only server_url exists, we'll use that in our code
            print("Using server_url column in erpnext_configs table")
            pass  # No need to rename, our code now adapts to use server_url
        elif 'url' in columns and 'server_url' not in columns:
            # If only url exists, we'll use that in our code
            print("Using url column in erpnext_configs table")
            pass  # No need to change, our code now adapts to use url
        elif 'server_url' not in columns and 'url' not in columns:
            # If neither exists, add server_url to match the NOT NULL constraint
            print("Adding server_url column to erpnext_configs table")
            cursor.execute("ALTER TABLE erpnext_configs ADD COLUMN server_url TEXT")
        # Otherwise both exist, which is fine with our dynamic code
        
        # Continue with other column checks
        if 'username' not in columns:
            cursor.execute("ALTER TABLE erpnext_configs ADD COLUMN username TEXT")
        if 'api_key_encrypted' not in columns:
            cursor.execute("ALTER TABLE erpnext_configs ADD COLUMN api_key_encrypted TEXT")
        if 'api_key_encryption_key' not in columns:
            cursor.execute("ALTER TABLE erpnext_configs ADD COLUMN api_key_encryption_key TEXT")
        # Add similar checks for other columns in erpnext_configs if needed
        
        # Migration: Add missing columns to company_configs if not exist
        cursor.execute("PRAGMA table_info(company_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'description' not in columns:
            cursor.execute("ALTER TABLE company_configs ADD COLUMN description TEXT")
        # Add similar checks for other missing columns
        
        conn.commit()
        conn.close()
    
    def encrypt_data(self, data: str) -> tuple:
        """Encrypt sensitive data"""
        key = Fernet.generate_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode(), base64.b64encode(key).decode()
    
    def decrypt_data(self, encrypted_data: str, key: str) -> str:
        """Decrypt sensitive data"""
        try:
            fernet = Fernet(base64.b64decode(key.encode()))
            decrypted_data = fernet.decrypt(base64.b64decode(encrypted_data.encode()))
            return decrypted_data.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

class UserManager:
    """User management operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == password_hash
    
    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create new user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                conn.close()
                return None
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, salt))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, is_active
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and user[5] and self.verify_password(password, user[3], user[4]):
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3]
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_profile(self, user_id: int, username: str = None, email: str = None) -> bool:
        """Update user profile"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if username:
                updates.append('username = ?')
                params.append(username)
            
            if email:
                updates.append('email = ?')
                params.append(email)
            
            if updates:
                updates.append('updated_at = ?')
                params.append(datetime.now())
                params.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                
                conn.commit()
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False

class SessionManager:
    """Session management operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_session(self, user_id: int) -> str:
        """Create new session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # 7 days expiry
            
            # Insert session
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            conn.commit()
            conn.close()
            
            return session_token
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[int]:
        """Validate session and return user ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id FROM sessions
                WHERE session_token = ? AND expires_at > ? AND is_active = 1
            ''', (session_token, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"Error validating session: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = 0
                WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error invalidating session: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = 0
                WHERE expires_at <= ?
            ''', (datetime.now(),))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")

class ConfigManager:
    """Configuration management operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_company_config(self, user_id: int, config: Dict[str, Any]) -> bool:
        """Save company configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if config exists
            cursor.execute('SELECT id FROM company_configs WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE company_configs SET
                    company_name = ?, industry = ?, website = ?, description = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (
                    config.get('company_name'),
                    config.get('industry'),
                    config.get('website'),
                    config.get('description'),
                    datetime.now(),
                    user_id
                ))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO company_configs (user_id, company_name, industry, website, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    config.get('company_name'),
                    config.get('industry'),
                    config.get('website'),
                    config.get('description')
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving company config: {e}")
            return False
    
    def get_company_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get company configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT company_name, industry, website, description
                FROM company_configs WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'company_name': result[0],
                    'industry': result[1],
                    'website': result[2],
                    'description': result[3]
                }
            return None
        except Exception as e:
            print(f"Error getting company config: {e}")
            return None
    
    def save_erpnext_config(self, user_id: int, config: Dict[str, Any]) -> bool:
        """Save ERPNext configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if the table has server_url column instead of url
            cursor.execute("PRAGMA table_info(erpnext_configs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Determine which column name to use
            url_column = 'server_url' if 'server_url' in columns else 'url'
            
            # Encrypt password
            encrypted_password, password_key = self.db.encrypt_data(config['password'])
            
            # Encrypt API key if provided
            encrypted_api_key = None
            api_key_key = None
            if config.get('api_key'):
                encrypted_api_key, api_key_key = self.db.encrypt_data(config['api_key'])
            
            # Check if config exists
            cursor.execute('SELECT id FROM erpnext_configs WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing - use dynamic column name
                query = f'''
                    UPDATE erpnext_configs SET
                    {url_column} = ?, username = ?, password_encrypted = ?, encryption_key = ?,
                    api_key_encrypted = ?, api_key_encryption_key = ?, updated_at = ?
                    WHERE user_id = ?
                '''
                cursor.execute(query, (
                    config['url'],
                    config['username'],
                    encrypted_password,
                    password_key,
                    encrypted_api_key,
                    api_key_key,
                    datetime.now(),
                    user_id
                ))
            else:
                # Insert new - use dynamic column name
                query = f'''
                    INSERT INTO erpnext_configs 
                    (user_id, {url_column}, username, password_encrypted, encryption_key, api_key_encrypted, api_key_encryption_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(query, (
                    user_id,
                    config['url'],
                    config['username'],
                    encrypted_password,
                    password_key,
                    encrypted_api_key,
                    api_key_key
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving ERPNext config: {e}")
            return False
    
    def get_erpnext_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get ERPNext configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if the table has server_url column instead of url
            cursor.execute("PRAGMA table_info(erpnext_configs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Determine which column name to use
            url_column = 'server_url' if 'server_url' in columns else 'url'
            
            # Use dynamic column name in query
            query = f'''
                SELECT {url_column}, username, password_encrypted, encryption_key, 
                       api_key_encrypted, api_key_encryption_key
                FROM erpnext_configs WHERE user_id = ? AND is_active = 1
            '''
            
            cursor.execute(query, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Decrypt password
                password = self.db.decrypt_data(result[2], result[3])
                
                # Decrypt API key if exists
                api_key = None
                if result[4] and result[5]:
                    api_key = self.db.decrypt_data(result[4], result[5])
                
                return {
                    'url': result[0],
                    'username': result[1],
                    'password': password,
                    'api_key': api_key
                }
            return None
        except Exception as e:
            print(f"Error getting ERPNext config: {e}")
            return None
    
    def get_lead_stats(self, user_id: int) -> Dict[str, Any]:
        """Get lead statistics for user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Total leads
            cursor.execute(
                "SELECT SUM(leads_generated) FROM lead_history WHERE user_id = ?",
                (user_id,)
            )
            total_leads = cursor.fetchone()[0] or 0
            
            # Today's leads
            cursor.execute(
                "SELECT SUM(leads_generated) FROM lead_history WHERE user_id = ? AND DATE(created_at) = DATE('now')",
                (user_id,)
            )
            today_leads = cursor.fetchone()[0] or 0
            
            # Synced leads
            cursor.execute(
                "SELECT SUM(leads_synced) FROM lead_history WHERE user_id = ?",
                (user_id,)
            )
            synced_leads = cursor.fetchone()[0] or 0
            
            # Conversion rate
            conversion_rate = (synced_leads / total_leads * 100) if total_leads > 0 else 0
            
            conn.close()
            
            return {
                'total_leads': total_leads,
                'today_leads': today_leads,
                'conversion_rate': round(conversion_rate, 1)
            }
        except Exception as e:
            print(f"Error getting lead stats: {e}")
            return {'total_leads': 0, 'today_leads': 0, 'conversion_rate': 0}
    
    def get_user_leads(self, user_id: int, limit=None) -> List[Dict[str, Any]]:
        """Get all individual leads for user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM leads WHERE user_id = ? ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            conn.close()
            
            leads = []
            for result in results:
                # Parse the data field if it exists
                data = {}
                if result[10]:  # data field (index 10)
                    try:
                        data = json.loads(result[10])
                    except:
                        data = {}
                
                leads.append({
                    'id': result[0],
                    'user_id': result[1],
                    'lead_history_id': result[2],
                    'name': result[3],
                    'address': result[4],
                    'phone': result[5],
                    'email': result[6],
                    'website': result[7],
                    'rating': result[8],
                    'category': result[9],
                    'data': data,
                    'is_synced': result[11],
                    'created_at': result[12],
                    'updated_at': result[13]
                })
            
            return leads
        except Exception as e:
            print(f"Error getting user leads: {e}")
            return []
    
    def get_recent_leads(self, user_id: int) -> List[Dict[str, Any]]:
        """Get leads from the most recent generation session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get the most recent lead_history_id for this user
            cursor.execute(
                "SELECT id FROM lead_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            recent_history = cursor.fetchone()
            
            if not recent_history:
                conn.close()
                return []
            
            recent_history_id = recent_history[0]
            
            # Get all leads from this recent session
            cursor.execute(
                "SELECT * FROM leads WHERE user_id = ? AND lead_history_id = ? ORDER BY created_at DESC",
                (user_id, recent_history_id)
            )
            results = cursor.fetchall()
            conn.close()
            
            leads = []
            for result in results:
                # Parse the data field if it exists
                data = {}
                if result[10]:  # data field (index 10)
                    try:
                        data = json.loads(result[10])
                    except:
                        data = {}
                
                leads.append({
                    'id': result[0],
                    'user_id': result[1],
                    'lead_history_id': result[2],
                    'name': result[3],
                    'address': result[4],
                    'phone': result[5],
                    'email': result[6],
                    'website': result[7],
                    'rating': result[8],
                    'category': result[9],
                    'data': data,
                    'is_synced': result[11],
                    'created_at': result[12],
                    'updated_at': result[13]
                })
            
            return leads
        except Exception as e:
            print(f"Error getting recent leads: {e}")
            return []
    
    def delete_lead(self, user_id: int, lead_id: int) -> bool:
        """Delete a lead for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM lead_history WHERE id = ? AND user_id = ?",
                (lead_id, user_id)
            )
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
        except Exception as e:
            print(f"Error deleting lead: {e}")
            return False
    
    def save_lead_generation(self, user_id: int, query: str, source: str, 
                           leads_generated: int = 0, leads_synced: int = 0) -> int:
        """Save a lead generation record and return the ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO lead_history (user_id, query, source, leads_generated, leads_synced) VALUES (?, ?, ?, ?, ?)",
                (user_id, query, source, leads_generated, leads_synced)
            )
            
            lead_history_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return lead_history_id
        except Exception as e:
            print(f"Error saving lead generation: {e}")
            return None
    
    def delete_lead(self, user_id: int, lead_id: int) -> bool:
        """Delete a lead for user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM lead_history WHERE id = ? AND user_id = ?",
                (lead_id, user_id)
            )
            
            conn.commit()
            result = cursor.rowcount > 0
            conn.close()
            return result
        except Exception as e:
            print(f"Error deleting lead: {e}")
            return False
    
    def get_unsynced_leads(self, user_id: int) -> List[Dict[str, Any]]:
        """Get unsynced leads for user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM lead_history WHERE user_id = ? AND leads_synced < leads_generated",
                (user_id,)
            )
            results = cursor.fetchall()
            conn.close()
            
            leads = []
            for result in results:
                leads.append({
                    'id': result[0],
                    'query': result[2],
                    'source': result[3],
                    'leads_generated': result[4],
                    'leads_synced': result[5],
                    'status': result[6],
                    'created_at': result[7]
                })
            
            return leads
        except Exception as e:
            print(f"Error getting unsynced leads: {e}")
            return []
    
    def mark_lead_synced(self, lead_id: int, synced_count: int = None) -> bool:
        """Mark a lead history as synced"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if synced_count is not None:
                cursor.execute(
                    "UPDATE lead_history SET leads_synced = ?, status = 'synced' WHERE id = ?",
                    (synced_count, lead_id)
                )
            else:
                cursor.execute(
                    "UPDATE lead_history SET leads_synced = leads_generated, status = 'synced' WHERE id = ?",
                    (lead_id,)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking lead as synced: {e}")
            return False
    
    def mark_individual_lead_synced(self, lead_id: int) -> bool:
        """Mark an individual lead as synced to CRM"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE leads SET is_synced = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (lead_id,)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking individual lead as synced: {e}")
            return False
    
    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT settings FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                import json
                return json.loads(result[0])
            return {}
        except Exception as e:
            print(f"Error getting user settings: {e}")
            return {}
    
    def save_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Save user settings"""
        try:
            import json
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if settings exist
            cursor.execute('SELECT id FROM user_settings WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            settings_json = json.dumps(settings)
            
            if existing:
                # Update existing
                cursor.execute(
                    'UPDATE user_settings SET settings = ?, updated_at = ? WHERE user_id = ?',
                    (settings_json, datetime.now(), user_id)
                )
            else:
                # Insert new
                cursor.execute(
                    'INSERT INTO user_settings (user_id, settings) VALUES (?, ?)',
                    (user_id, settings_json)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving user settings: {e}")
            return False
    
    def save_individual_leads(self, user_id: int, lead_history_id: int, leads_data: List[Dict[str, Any]]) -> bool:
        """Save individual leads to the leads table"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for lead in leads_data:
                cursor.execute(
                    """INSERT INTO leads (user_id, lead_history_id, name, address, phone, email, website, rating, category, data) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        lead_history_id,
                        lead.get('company_name', lead.get('name', '')),  # Use company_name first, fallback to name
                        lead.get('address', ''),
                        lead.get('phone', ''),
                        lead.get('email', ''),
                        lead.get('website', ''),
                        lead.get('rating', 0),
                        lead.get('category', ''),
                        json.dumps(lead)
                    )
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving individual leads: {e}")
            return False
    
    def get_lead_by_id(self, user_id: int, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific lead by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM leads WHERE id = ? AND user_id = ?",
                (lead_id, user_id)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Parse the data field if it exists
                data = {}
                if result[10]:  # data field (index 10)
                    try:
                        data = json.loads(result[10])
                    except:
                        data = {}
                
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'lead_history_id': result[2],
                    'name': result[3],
                    'address': result[4],
                    'phone': result[5],
                    'email': result[6],
                    'website': result[7],
                    'rating': result[8],
                    'category': result[9],
                    'data': data,
                    'is_synced': result[11],
                    'created_at': result[12],
                    'updated_at': result[13]
                }
            
            return None
        except Exception as e:
            print(f"Error getting lead by ID: {e}")
            return None

    def save_imported_lead(self, user_id: int, lead_data: Dict[str, Any]) -> Optional[int]:
        """Save an imported CRM lead to the local database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if lead already exists (by email or name)
            existing_lead = None
            if lead_data.get('email'):
                cursor.execute(
                    "SELECT id FROM leads WHERE user_id = ? AND email = ?",
                    (user_id, lead_data['email'])
                )
                existing_lead = cursor.fetchone()
            
            if not existing_lead and lead_data.get('name'):
                cursor.execute(
                    "SELECT id FROM leads WHERE user_id = ? AND name = ?",
                    (user_id, lead_data['name'])
                )
                existing_lead = cursor.fetchone()
            
            if existing_lead:
                # Update existing lead
                cursor.execute('''
                    UPDATE leads SET 
                        address = ?, phone = ?, email = ?, website = ?, 
                        category = ?, data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    lead_data.get('address', ''),
                    lead_data.get('phone', ''),
                    lead_data.get('email', ''),
                    lead_data.get('website', ''),
                    lead_data.get('category', ''),
                    json.dumps(lead_data),
                    existing_lead[0]
                ))
                conn.commit()
                conn.close()
                return existing_lead[0]
            
            # Create new lead
            cursor.execute('''
                INSERT INTO leads (
                    user_id, lead_history_id, name, address, phone, email, 
                    website, rating, category, data, is_synced, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                0,  # No lead_history_id for imported leads
                lead_data.get('name', ''),
                lead_data.get('address', ''),
                lead_data.get('phone', ''),
                lead_data.get('email', ''),
                lead_data.get('website', ''),
                lead_data.get('rating', ''),
                lead_data.get('category', ''),
                json.dumps(lead_data),
                1  # Mark as synced since it came from CRM
            ))
            
            lead_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return lead_id
        except Exception as e:
            print(f"Error saving imported lead: {e}")
            return None

    # Email Template Management Methods
    def save_email_template(self, user_id: int, template_data: Dict[str, Any]) -> Optional[int]:
        """Save an email template for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_templates (
                    user_id, name, subject, content, variables, category, 
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                template_data.get('name', ''),
                template_data.get('subject', ''),
                template_data.get('content', ''),
                json.dumps(template_data.get('variables', {})),
                template_data.get('category', 'General'),
                1
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return template_id
        except Exception as e:
            print(f"Error saving email template: {e}")
            return None

    def get_email_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all email templates for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, subject, content, variables, category, 
                       is_active, created_at, updated_at
                FROM email_templates 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            templates = []
            for result in results:
                # Parse variables JSON
                variables = {}
                if result[4]:  # variables field
                    try:
                        variables = json.loads(result[4])
                    except:
                        variables = {}
                
                templates.append({
                    'id': result[0],
                    'name': result[1],
                    'subject': result[2],
                    'content': result[3],
                    'variables': variables,
                    'category': result[5],
                    'is_active': bool(result[6]),
                    'created_at': result[7],
                    'updated_at': result[8]
                })
            
            return templates
        except Exception as e:
            print(f"Error getting email templates: {e}")
            return []

    def get_email_template_by_id(self, user_id: int, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific email template by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, subject, content, variables, category, 
                       is_active, created_at, updated_at
                FROM email_templates 
                WHERE id = ? AND user_id = ?
            ''', (template_id, user_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Parse variables JSON
                variables = {}
                if result[4]:  # variables field
                    try:
                        variables = json.loads(result[4])
                    except:
                        variables = {}
                
                return {
                    'id': result[0],
                    'name': result[1],
                    'subject': result[2],
                    'content': result[3],
                    'variables': variables,
                    'category': result[5],
                    'is_active': bool(result[6]),
                    'created_at': result[7],
                    'updated_at': result[8]
                }
            
            return None
        except Exception as e:
            print(f"Error getting email template by ID: {e}")
            return None

    def update_email_template(self, user_id: int, template_id: int, template_data: Dict[str, Any]) -> bool:
        """Update an email template"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE email_templates SET 
                    name = ?, subject = ?, content = ?, variables = ?, 
                    category = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (
                template_data.get('name', ''),
                template_data.get('subject', ''),
                template_data.get('content', ''),
                json.dumps(template_data.get('variables', {})),
                template_data.get('category', 'General'),
                template_data.get('is_active', True),
                template_id,
                user_id
            ))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating email template: {e}")
            return False

    def delete_email_template(self, user_id: int, template_id: int) -> bool:
        """Delete an email template"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM email_templates 
                WHERE id = ? AND user_id = ?
            ''', (template_id, user_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting email template: {e}")
            return False

    # Email Campaign Management Methods
    def save_email_campaign(self, user_id: int, campaign_data: Dict[str, Any]) -> Optional[int]:
        """Save an email campaign"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_campaigns (
                    user_id, name, description, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                campaign_data.get('name', ''),
                campaign_data.get('description', ''),
                campaign_data.get('status', 'draft')
            ))
            
            campaign_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return campaign_id
        except Exception as e:
            print(f"Error saving email campaign: {e}")
            return None

    def get_email_campaigns(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all email campaigns for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, description, status, created_at, updated_at
                FROM email_campaigns 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            campaigns = []
            for result in results:
                campaigns.append({
                    'id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'status': result[3],
                    'created_at': result[4],
                    'updated_at': result[5]
                })
            
            return campaigns
        except Exception as e:
            print(f"Error getting email campaigns: {e}")
            return []

    # Email Sequence Management Methods
    def save_email_sequence(self, user_id: int, sequence_data: Dict[str, Any]) -> Optional[int]:
        """Save an email sequence"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_sequences (
                    user_id, campaign_id, name, description, steps, triggers, 
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                sequence_data.get('campaign_id'),
                sequence_data.get('name', ''),
                sequence_data.get('description', ''),
                json.dumps(sequence_data.get('steps', [])),
                json.dumps(sequence_data.get('triggers', {})),
                sequence_data.get('is_active', True)
            ))
            
            sequence_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return sequence_id
        except Exception as e:
            print(f"Error saving email sequence: {e}")
            return None

    def get_email_sequences(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all email sequences for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, campaign_id, name, description, steps, triggers, 
                       is_active, created_at, updated_at
                FROM email_sequences 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            sequences = []
            for result in results:
                # Parse JSON fields
                steps = {}
                triggers = {}
                if result[4]:  # steps field
                    try:
                        steps = json.loads(result[4])
                    except:
                        steps = {}
                if result[5]:  # triggers field
                    try:
                        triggers = json.loads(result[5])
                    except:
                        triggers = {}
                
                sequences.append({
                    'id': result[0],
                    'campaign_id': result[1],
                    'name': result[2],
                    'description': result[3],
                    'steps': steps,
                    'triggers': triggers,
                    'is_active': bool(result[6]),
                    'created_at': result[7],
                    'updated_at': result[8]
                })
            
            return sequences
        except Exception as e:
            print(f"Error getting email sequences: {e}")
            return []

    # Email Tracking Methods
    def create_email_tracking(self, user_id: int, tracking_data: Dict[str, Any]) -> Optional[int]:
        """Create a new email tracking record"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Generate unique tracking ID
            import uuid
            tracking_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO email_tracking (
                    user_id, campaign_id, sequence_id, lead_id, email_address, 
                    subject, template_id, tracking_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                tracking_data.get('campaign_id'),
                tracking_data.get('sequence_id'),
                tracking_data.get('lead_id'),
                tracking_data.get('email_address', ''),
                tracking_data.get('subject', ''),
                tracking_data.get('template_id'),
                tracking_id
            ))
            
            tracking_record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return tracking_record_id
        except Exception as e:
            print(f"Error creating email tracking: {e}")
            return None

    def update_email_tracking_event(self, tracking_id: str, event_type: str, event_data: Dict[str, Any] = None) -> bool:
        """Update email tracking with an event"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get the tracking record
            cursor.execute('SELECT id FROM email_tracking WHERE tracking_id = ?', (tracking_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            tracking_record_id = result[0]
            
            # Update the main tracking record
            update_fields = []
            update_values = []
            
            if event_type == 'sent':
                update_fields.append('sent_at = CURRENT_TIMESTAMP')
            elif event_type == 'delivered':
                update_fields.append('delivered_at = CURRENT_TIMESTAMP')
            elif event_type == 'opened':
                update_fields.append('opened_at = CURRENT_TIMESTAMP')
                update_fields.append('open_count = open_count + 1')
            elif event_type == 'clicked':
                update_fields.append('clicked_at = CURRENT_TIMESTAMP')
                update_fields.append('click_count = click_count + 1')
            elif event_type == 'replied':
                update_fields.append('replied_at = CURRENT_TIMESTAMP')
            elif event_type == 'bounced':
                update_fields.append('bounced_at = CURRENT_TIMESTAMP')
            elif event_type == 'unsubscribed':
                update_fields.append('unsubscribed_at = CURRENT_TIMESTAMP')
            elif event_type == 'spam_reported':
                update_fields.append('spam_reported_at = CURRENT_TIMESTAMP')
            
            if update_fields:
                update_fields.append('updated_at = CURRENT_TIMESTAMP')
                query = f"UPDATE email_tracking SET {', '.join(update_fields)} WHERE tracking_id = ?"
                cursor.execute(query, (tracking_id,))
            
            # Add event to tracking events table
            cursor.execute('''
                INSERT INTO email_tracking_events (
                    tracking_id, event_type, event_data, created_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                tracking_record_id,
                event_type,
                json.dumps(event_data or {})
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error updating email tracking event: {e}")
            return False

    def get_email_tracking_by_id(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """Get email tracking record by tracking ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, campaign_id, sequence_id, lead_id, email_address,
                       subject, template_id, status, sent_at, delivered_at, opened_at,
                       clicked_at, replied_at, bounced_at, unsubscribed_at, spam_reported_at,
                       tracking_id, open_count, click_count, created_at, updated_at
                FROM email_tracking 
                WHERE tracking_id = ?
            ''', (tracking_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'campaign_id': result[2],
                    'sequence_id': result[3],
                    'lead_id': result[4],
                    'email_address': result[5],
                    'subject': result[6],
                    'template_id': result[7],
                    'status': result[8],
                    'sent_at': result[9],
                    'delivered_at': result[10],
                    'opened_at': result[11],
                    'clicked_at': result[12],
                    'replied_at': result[13],
                    'bounced_at': result[14],
                    'unsubscribed_at': result[15],
                    'spam_reported_at': result[16],
                    'tracking_id': result[17],
                    'open_count': result[18],
                    'click_count': result[19],
                    'created_at': result[20],
                    'updated_at': result[21]
                }
            
            return None
        except Exception as e:
            print(f"Error getting email tracking by ID: {e}")
            return None

    def get_email_tracking_events(self, tracking_id: str) -> List[Dict[str, Any]]:
        """Get all events for a tracking ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT event_type, event_data, ip_address, user_agent, location, created_at
                FROM email_tracking_events 
                WHERE tracking_id = (SELECT id FROM email_tracking WHERE tracking_id = ?)
                ORDER BY created_at ASC
            ''', (tracking_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            events = []
            for result in results:
                # Parse event_data JSON
                event_data = {}
                if result[1]:  # event_data field
                    try:
                        event_data = json.loads(result[1])
                    except:
                        event_data = {}
                
                events.append({
                    'event_type': result[0],
                    'event_data': event_data,
                    'ip_address': result[2],
                    'user_agent': result[3],
                    'location': result[4],
                    'created_at': result[5]
                })
            
            return events
        except Exception as e:
            print(f"Error getting email tracking events: {e}")
            return []

    # Email Sequence Instance Management
    def create_sequence_instance(self, user_id: int, sequence_id: int, lead_id: int) -> Optional[int]:
        """Create a new sequence instance for a lead"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_sequence_instances (
                    user_id, sequence_id, lead_id, current_step, status,
                    started_at, created_at, updated_at
                ) VALUES (?, ?, ?, 0, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, sequence_id, lead_id))
            
            instance_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return instance_id
        except Exception as e:
            print(f"Error creating sequence instance: {e}")
            return None

    def update_sequence_instance(self, instance_id: int, update_data: Dict[str, Any]) -> bool:
        """Update a sequence instance"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            update_fields = []
            update_values = []
            
            if 'current_step' in update_data:
                update_fields.append('current_step = ?')
                update_values.append(update_data['current_step'])
            
            if 'status' in update_data:
                update_fields.append('status = ?')
                update_values.append(update_data['status'])
            
            if 'next_step_due' in update_data:
                update_fields.append('next_step_due = ?')
                update_values.append(update_data['next_step_due'])
            
            if update_data.get('status') == 'completed':
                update_fields.append('completed_at = CURRENT_TIMESTAMP')
            elif update_data.get('status') == 'paused':
                update_fields.append('paused_at = CURRENT_TIMESTAMP')
            elif update_data.get('status') == 'active' and update_data.get('resumed'):
                update_fields.append('resumed_at = CURRENT_TIMESTAMP')
            
            if update_fields:
                update_fields.append('updated_at = CURRENT_TIMESTAMP')
                update_values.append(instance_id)
                
                query = f"UPDATE email_sequence_instances SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                conn.close()
                return True
            
            return False
        except Exception as e:
            print(f"Error updating sequence instance: {e}")
            return False

    def get_active_sequence_instances(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active sequence instances for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, sequence_id, lead_id, current_step, status, 
                       started_at, next_step_due, created_at
                FROM email_sequence_instances 
                WHERE user_id = ? AND status = 'active'
                ORDER BY next_step_due ASC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            instances = []
            for result in results:
                instances.append({
                    'id': result[0],
                    'sequence_id': result[1],
                    'lead_id': result[2],
                    'current_step': result[3],
                    'status': result[4],
                    'started_at': result[5],
                    'next_step_due': result[6],
                    'created_at': result[7]
                })
            
            return instances
        except Exception as e:
            print(f"Error getting active sequence instances: {e}")
            return []

    # Email Analytics Methods
    def get_email_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get email analytics for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_emails,
                    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_emails,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_emails,
                    COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END) as replied_emails,
                    COUNT(CASE WHEN bounced_at IS NOT NULL THEN 1 END) as bounced_emails,
                    COUNT(CASE WHEN unsubscribed_at IS NOT NULL THEN 1 END) as unsubscribed_emails,
                    SUM(open_count) as total_opens,
                    SUM(click_count) as total_clicks
                FROM email_tracking 
                WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
            '''.format(days), (user_id,))
            
            stats = cursor.fetchone()
            conn.close()
            
            if stats:
                total_emails = stats[0] or 0
                opened_emails = stats[1] or 0
                clicked_emails = stats[2] or 0
                replied_emails = stats[3] or 0
                bounced_emails = stats[4] or 0
                unsubscribed_emails = stats[5] or 0
                total_opens = stats[6] or 0
                total_clicks = stats[7] or 0
                
                return {
                    'total_emails': total_emails,
                    'opened_emails': opened_emails,
                    'clicked_emails': clicked_emails,
                    'replied_emails': replied_emails,
                    'bounced_emails': bounced_emails,
                    'unsubscribed_emails': unsubscribed_emails,
                    'total_opens': total_opens,
                    'total_clicks': total_clicks,
                    'open_rate': (opened_emails / total_emails * 100) if total_emails > 0 else 0,
                    'click_rate': (clicked_emails / total_emails * 100) if total_emails > 0 else 0,
                    'reply_rate': (replied_emails / total_emails * 100) if total_emails > 0 else 0,
                    'bounce_rate': (bounced_emails / total_emails * 100) if total_emails > 0 else 0,
                    'unsubscribe_rate': (unsubscribed_emails / total_emails * 100) if total_emails > 0 else 0
                }
            
            return {}
        except Exception as e:
            print(f"Error getting email analytics: {e}")
            return {}
    
    # Email Server Configuration Methods
    def save_email_server_config(self, user_id: int, config_data: Dict[str, Any]) -> Optional[int]:
        """Save email server configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_server_configs (
                    user_id, name, smtp_server, smtp_port, sender_email, 
                    sender_password, sender_name, use_ssl, use_tls, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                config_data.get('name', ''),
                config_data.get('smtp_server', ''),
                config_data.get('smtp_port', 587),
                config_data.get('sender_email', ''),
                config_data.get('sender_password', ''),
                config_data.get('sender_name', 'Aida Lead Intelligence'),
                config_data.get('use_ssl', False),
                config_data.get('use_tls', True),
                config_data.get('is_active', True)
            ))
            
            config_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return config_id
        except Exception as e:
            print(f"Error saving email server config: {e}")
            return None

    def get_email_server_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all email server configurations for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, smtp_server, smtp_port, sender_email, 
                       sender_name, use_ssl, use_tls, is_active, created_at, updated_at
                FROM email_server_configs 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            configs = []
            for result in results:
                configs.append({
                    'id': result[0],
                    'name': result[1],
                    'smtp_server': result[2],
                    'smtp_port': result[3],
                    'sender_email': result[4],
                    'sender_name': result[5],
                    'use_ssl': bool(result[6]),
                    'use_tls': bool(result[7]),
                    'is_active': bool(result[8]),
                    'created_at': result[9],
                    'updated_at': result[10]
                })
            
            return configs
        except Exception as e:
            print(f"Error getting email server configs: {e}")
            return []

    def get_email_server_config_by_id(self, user_id: int, config_id: int) -> Optional[Dict[str, Any]]:
        """Get specific email server configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, smtp_server, smtp_port, sender_email, 
                       sender_password, sender_name, use_ssl, use_tls, is_active,
                       created_at, updated_at
                FROM email_server_configs 
                WHERE id = ? AND user_id = ?
            ''', (config_id, user_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'smtp_server': result[2],
                    'smtp_port': result[3],
                    'sender_email': result[4],
                    'sender_password': result[5],
                    'sender_name': result[6],
                    'use_ssl': bool(result[7]),
                    'use_tls': bool(result[8]),
                    'is_active': bool(result[9]),
                    'created_at': result[10],
                    'updated_at': result[11]
                }
            
            return None
        except Exception as e:
            print(f"Error getting email server config: {e}")
            return None

    def update_email_server_config(self, user_id: int, config_id: int, config_data: Dict[str, Any]) -> bool:
        """Update email server configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE email_server_configs SET
                    name = ?, smtp_server = ?, smtp_port = ?, sender_email = ?,
                    sender_password = ?, sender_name = ?, use_ssl = ?, use_tls = ?,
                    is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (
                config_data.get('name', ''),
                config_data.get('smtp_server', ''),
                config_data.get('smtp_port', 587),
                config_data.get('sender_email', ''),
                config_data.get('sender_password', ''),
                config_data.get('sender_name', 'Aida Lead Intelligence'),
                config_data.get('use_ssl', False),
                config_data.get('use_tls', True),
                config_data.get('is_active', True),
                config_id,
                user_id
            ))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating email server config: {e}")
            return False

    def delete_email_server_config(self, user_id: int, config_id: int) -> bool:
        """Delete email server configuration"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM email_server_configs 
                WHERE id = ? AND user_id = ?
            ''', (config_id, user_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting email server config: {e}")
            return False

    def get_active_email_server_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the active email server configuration for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM email_server_configs WHERE user_id = ? AND is_active = 1 LIMIT 1",
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'name': result[2],
                    'smtp_server': result[3],
                    'smtp_port': result[4],
                    'sender_email': result[5],
                    'sender_password': result[6],
                    'sender_name': result[7],
                    'use_ssl': bool(result[8]),
                    'use_tls': bool(result[9]),
                    'is_active': bool(result[10]),
                    'created_at': result[11],
                    'updated_at': result[12]
                }
            
            return None
        except Exception as e:
            print(f"Error getting active email server config: {e}")
            return None

    def save_lead_score(self, user_id: int, lead_id: int, scoring_data: Dict[str, Any]) -> Optional[int]:
        """Save lead scoring data"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if score already exists
            cursor.execute(
                "SELECT id FROM lead_scores WHERE user_id = ? AND lead_id = ?",
                (user_id, lead_id)
            )
            existing_score = cursor.fetchone()
            
            if existing_score:
                # Update existing score
                cursor.execute('''
                    UPDATE lead_scores 
                    SET score = ?, status = ?, factors = ?, recommendations = ?, 
                        confidence = ?, reasoning = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND lead_id = ?
                ''', (
                    scoring_data.get('score', 0),
                    scoring_data.get('status', 'COLD'),
                    json.dumps(scoring_data.get('factors', {})),
                    scoring_data.get('recommendations', ''),
                    scoring_data.get('confidence', 'LOW'),
                    scoring_data.get('reasoning', ''),
                    user_id,
                    lead_id
                ))
                score_id = existing_score[0]
            else:
                # Insert new score
                cursor.execute('''
                    INSERT INTO lead_scores (user_id, lead_id, score, status, factors, recommendations, confidence, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    lead_id,
                    scoring_data.get('score', 0),
                    scoring_data.get('status', 'COLD'),
                    json.dumps(scoring_data.get('factors', {})),
                    scoring_data.get('recommendations', ''),
                    scoring_data.get('confidence', 'LOW'),
                    scoring_data.get('reasoning', '')
                ))
                score_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return score_id
            
        except Exception as e:
            print(f"Error saving lead score: {e}")
            return None

    def get_lead_score(self, user_id: int, lead_id: int) -> Optional[Dict[str, Any]]:
        """Get lead scoring data"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM lead_scores WHERE user_id = ? AND lead_id = ?",
                (user_id, lead_id)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'lead_id': result[1],
                    'user_id': result[2],
                    'score': result[3],
                    'status': result[4],
                    'factors': json.loads(result[5]) if result[5] else {},
                    'recommendations': result[6],
                    'confidence': result[7],
                    'reasoning': result[8],
                    'scored_at': result[9],
                    'updated_at': result[10]
                }
            
            return None
        except Exception as e:
            print(f"Error getting lead score: {e}")
            return None

    def get_user_lead_scores(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """Get all lead scores for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT ls.*, l.name as lead_name, l.email, l.phone
                FROM lead_scores ls
                JOIN leads l ON ls.lead_id = l.id
                WHERE ls.user_id = ?
                ORDER BY ls.scored_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            conn.close()
            
            scores = []
            for result in results:
                scores.append({
                    'id': result[0],
                    'lead_id': result[1],
                    'user_id': result[2],
                    'score': result[3],
                    'status': result[4],
                    'factors': json.loads(result[5]) if result[5] else {},
                    'recommendations': result[6],
                    'confidence': result[7],
                    'reasoning': result[8],
                    'scored_at': result[9],
                    'updated_at': result[10],
                    'lead_name': result[11],
                    'email': result[12],
                    'phone': result[13]
                })
            
            return scores
        except Exception as e:
            print(f"Error getting user lead scores: {e}")
            return []

    def get_lead_scoring_summary(self, user_id: int) -> Dict[str, Any]:
        """Get lead scoring summary statistics for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get total leads with scores
            cursor.execute(
                "SELECT COUNT(*) FROM lead_scores WHERE user_id = ?",
                (user_id,)
            )
            total_leads = cursor.fetchone()[0]
            
            if total_leads == 0:
                return {
                    "total_leads": 0,
                    "hot_leads": 0,
                    "warm_leads": 0,
                    "cold_leads": 0,
                    "average_score": 0,
                    "score_distribution": {}
                }
            
            # Get score distribution
            cursor.execute(
                "SELECT status, COUNT(*) FROM lead_scores WHERE user_id = ? GROUP BY status",
                (user_id,)
            )
            status_counts = dict(cursor.fetchall())
            
            # Get average score
            cursor.execute(
                "SELECT AVG(score) FROM lead_scores WHERE user_id = ?",
                (user_id,)
            )
            average_score = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_leads": total_leads,
                "hot_leads": status_counts.get('HOT', 0),
                "warm_leads": status_counts.get('WARM', 0),
                "cold_leads": status_counts.get('COLD', 0),
                "average_score": round(average_score, 2),
                "score_distribution": {
                    "hot_percentage": round((status_counts.get('HOT', 0) / total_leads) * 100, 2),
                    "warm_percentage": round((status_counts.get('WARM', 0) / total_leads) * 100, 2),
                    "cold_percentage": round((status_counts.get('COLD', 0) / total_leads) * 100, 2)
                }
            }
        except Exception as e:
            print(f"Error getting lead scoring summary: {e}")
            return {
                "total_leads": 0,
                "hot_leads": 0,
                "warm_leads": 0,
                "cold_leads": 0,
                "average_score": 0,
                "score_distribution": {}
            }