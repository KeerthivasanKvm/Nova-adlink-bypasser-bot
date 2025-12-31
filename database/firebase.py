"""
Firebase Firestore Database Handler
Manages database connections and operations using Firebase
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter

from config import Config

logger = logging.getLogger(__name__)


class FirebaseDB:
    """Firebase Firestore connection and operations handler"""
    
    _instance: Optional['FirebaseDB'] = None
    _db = None
    _app = None
    
    def __new__(cls):
        """Singleton pattern to ensure single database connection"""
        if cls._instance is None:
            cls._instance = super(FirebaseDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase connection"""
        if self._db is None:
            self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection to Firebase Firestore
        Returns True if successful, False otherwise
        """
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # Initialize Firebase with credentials
                cred_path = Config.FIREBASE_CREDENTIALS
                
                if not os.path.exists(cred_path):
                    logger.error(f"❌ Firebase credentials file not found: {cred_path}")
                    return False
                
                cred = credentials.Certificate(cred_path)
                self._app = firebase_admin.initialize_app(cred, {
                    'projectId': Config.FIREBASE_PROJECT_ID
                })
                
                logger.info("✅ Firebase app initialized")
            
            # Get Firestore client
            self._db = firestore.client()
            
            # Test connection by attempting to read
            test_ref = self._db.collection('_test').document('connection')
            test_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
            test_ref.delete()
            
            # Initialize default data
            self._initialize_defaults()
            
            logger.info("✅ Firebase Firestore connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Firebase connection failed: {e}")
            return False
    
    def _initialize_defaults(self):
        """Initialize default data in Firestore"""
        try:
            # Add default supported sites
            sites_ref = self._db.collection(Config.SITES_COLLECTION)
            
            for domain in Config.DEFAULT_SUPPORTED_DOMAINS:
                doc_ref = sites_ref.document(domain)
                doc = doc_ref.get()
                
                if not doc.exists:
                    doc_ref.set({
                        'domain': domain,
                        'is_active': True,
                        'added_at': firestore.SERVER_TIMESTAMP,
                        'added_by': Config.OWNER_ID,
                        'bypass_count': 0
                    })
            
            logger.info("✅ Default data initialized in Firebase")
            
        except Exception as e:
            logger.error(f"❌ Error initializing defaults: {e}")
    
    @property
    def db(self):
        """Get Firestore database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    def close(self):
        """Close Firebase connection"""
        if self._app:
            firebase_admin.delete_app(self._app)
            logger.info("📴 Firebase connection closed")
    
    # User Operations
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user"""
        try:
            user_id = str(user_data.get('user_id'))
            user_ref = self.db.collection(Config.USERS_COLLECTION).document(user_id)
            
            # Check if user exists
            if user_ref.get().exists:
                logger.warning(f"⚠️ User {user_id} already exists")
                return False
            
            # Set default values
            user_data.setdefault('created_at', firestore.SERVER_TIMESTAMP)
            user_data.setdefault('is_premium', False)
            user_data.setdefault('is_banned', False)
            user_data.setdefault('bypass_count', 0)
            user_data.setdefault('daily_bypass_count', 0)
            user_data.setdefault('monthly_bypass_count', 0)
            user_data.setdefault('last_reset_date', datetime.utcnow().date().isoformat())
            user_data.setdefault('referral_code', None)
            user_data.setdefault('referred_by', None)
            user_data.setdefault('referral_count', 0)
            
            user_ref.set(user_data)
            logger.info(f"✅ User {user_id} created in Firebase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user_ref = self.db.collection(Config.USERS_COLLECTION).document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            user_ref = self.db.collection(Config.USERS_COLLECTION).document(str(user_id))
            
            # Check if user exists
            if not user_ref.get().exists:
                logger.warning(f"⚠️ User {user_id} not found")
                return False
            
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.update(update_data)
            logger.info(f"✅ User {user_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            return False
    
    def increment_bypass_count(self, user_id: int) -> bool:
        """Increment user bypass counters"""
        try:
            user_ref = self.db.collection(Config.USERS_COLLECTION).document(str(user_id))
            
            user_ref.update({
                'bypass_count': firestore.Increment(1),
                'daily_bypass_count': firestore.Increment(1),
                'monthly_bypass_count': firestore.Increment(1),
                'last_bypass_at': firestore.SERVER_TIMESTAMP
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error incrementing bypass count: {e}")
            return False
    
    def reset_daily_limits(self):
        """Reset daily limits for all users"""
        try:
            users_ref = self.db.collection(Config.USERS_COLLECTION)
            users = users_ref.stream()
            
            batch = self.db.batch()
            count = 0
            
            for user in users:
                user_ref = users_ref.document(user.id)
                batch.update(user_ref, {
                    'daily_bypass_count': 0,
                    'last_reset_date': datetime.utcnow().date().isoformat()
                })
                count += 1
                
                # Commit batch every 500 operations (Firestore limit)
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining operations
            if count % 500 != 0:
                batch.commit()
            
            logger.info(f"✅ Daily limits reset for {count} users")
            
        except Exception as e:
            logger.error(f"❌ Error resetting daily limits: {e}")
    
    # Cache Operations
    def get_cached_bypass(self, original_url: str) -> Optional[str]:
        """Get cached bypass result"""
        try:
            # Create a safe document ID from URL
            doc_id = abs(hash(original_url)) % (10 ** 10)
            cache_ref = self.db.collection(Config.CACHE_COLLECTION).document(str(doc_id))
            cache_doc = cache_ref.get()
            
            if cache_doc.exists:
                cache_data = cache_doc.to_dict()
                created_at = cache_data.get('created_at')
                
                # Check if cache is still valid
                if created_at:
                    expiry = created_at + timedelta(hours=Config.CACHE_EXPIRY_HOURS)
                    if datetime.utcnow() < expiry:
                        # Increment hit count
                        cache_ref.update({'hit_count': firestore.Increment(1)})
                        logger.info(f"✅ Cache hit for: {original_url}")
                        return cache_data.get('bypassed_url')
                    else:
                        # Cache expired, delete it
                        cache_ref.delete()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting cached bypass: {e}")
            return None
    
    def cache_bypass(self, original_url: str, bypassed_url: str, method: str = None) -> bool:
        """Cache bypass result"""
        try:
            doc_id = abs(hash(original_url)) % (10 ** 10)
            cache_ref = self.db.collection(Config.CACHE_COLLECTION).document(str(doc_id))
            
            cache_ref.set({
                'original_url': original_url,
                'bypassed_url': bypassed_url,
                'method_used': method,
                'created_at': datetime.utcnow(),
                'hit_count': 1
            })
            
            logger.info(f"✅ Cached bypass for: {original_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error caching bypass: {e}")
            return False
    
    # Token Operations
    def create_token(self, token_data: Dict[str, Any]) -> bool:
        """Create access token"""
        try:
            token = token_data.get('token')
            token_ref = self.db.collection(Config.TOKENS_COLLECTION).document(token)
            
            # Check if token exists
            if token_ref.get().exists:
                logger.warning("⚠️ Token already exists")
                return False
            
            token_data.setdefault('created_at', firestore.SERVER_TIMESTAMP)
            token_data.setdefault('is_used', False)
            token_data.setdefault('used_by', None)
            token_data.setdefault('used_at', None)
            
            token_ref.set(token_data)
            logger.info(f"✅ Token created: {token}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating token: {e}")
            return False
    
    def get_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token by value"""
        try:
            token_ref = self.db.collection(Config.TOKENS_COLLECTION).document(token)
            token_doc = token_ref.get()
            
            if token_doc.exists:
                return token_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting token: {e}")
            return None
    
    def use_token(self, token: str, user_id: int) -> bool:
        """Mark token as used"""
        try:
            token_ref = self.db.collection(Config.TOKENS_COLLECTION).document(token)
            token_doc = token_ref.get()
            
            if not token_doc.exists:
                return False
            
            token_data = token_doc.to_dict()
            if token_data.get('is_used', False):
                return False
            
            token_ref.update({
                'is_used': True,
                'used_by': user_id,
                'used_at': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"✅ Token {token} used by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error using token: {e}")
            return False
    
    # Site Operations
    def add_site(self, domain: str, added_by: int) -> bool:
        """Add supported site"""
        try:
            site_ref = self.db.collection(Config.SITES_COLLECTION).document(domain)
            
            site_ref.set({
                'domain': domain,
                'is_active': True,
                'added_at': firestore.SERVER_TIMESTAMP,
                'added_by': added_by,
                'bypass_count': 0
            }, merge=True)
            
            logger.info(f"✅ Site added: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding site: {e}")
            return False
    
    def remove_site(self, domain: str) -> bool:
        """Remove supported site"""
        try:
            site_ref = self.db.collection(Config.SITES_COLLECTION).document(domain)
            
            if not site_ref.get().exists:
                return False
            
            site_ref.update({'is_active': False})
            logger.info(f"✅ Site removed: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing site: {e}")
            return False
    
    def get_active_sites(self) -> List[str]:
        """Get all active sites"""
        try:
            sites_ref = self.db.collection(Config.SITES_COLLECTION)
            query = sites_ref.where(filter=FieldFilter('is_active', '==', True))
            sites = query.stream()
            
            return [site.to_dict()['domain'] for site in sites]
            
        except Exception as e:
            logger.error(f"❌ Error getting active sites: {e}")
            return []
    
    # Group Operations
    def add_group(self, group_id: int, group_title: str, added_by: int) -> bool:
        """Add allowed group"""
        try:
            group_ref = self.db.collection(Config.GROUPS_COLLECTION).document(str(group_id))
            
            group_ref.set({
                'group_id': group_id,
                'group_title': group_title,
                'is_active': True,
                'added_at': firestore.SERVER_TIMESTAMP,
                'added_by': added_by
            })
            
            logger.info(f"✅ Group added: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding group: {e}")
            return False
    
    def remove_group(self, group_id: int) -> bool:
        """Remove group"""
        try:
            group_ref = self.db.collection(Config.GROUPS_COLLECTION).document(str(group_id))
            
            if not group_ref.get().exists:
                return False
            
            group_ref.update({'is_active': False})
            logger.info(f"✅ Group removed: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing group: {e}")
            return False
    
    def is_group_allowed(self, group_id: int) -> bool:
        """Check if group is allowed"""
        try:
            group_ref = self.db.collection(Config.GROUPS_COLLECTION).document(str(group_id))
            group_doc = group_ref.get()
            
            if group_doc.exists:
                group_data = group_doc.to_dict()
                return group_data.get('is_active', False)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking group: {e}")
            return False
    
    # Statistics
    def get_total_users(self) -> int:
        """Get total user count"""
        try:
            users_ref = self.db.collection(Config.USERS_COLLECTION)
            users = list(users_ref.stream())
            return len(users)
            
        except Exception as e:
            logger.error(f"❌ Error getting user count: {e}")
            return 0
    
    def get_premium_users_count(self) -> int:
        """Get premium users count"""
        try:
            users_ref = self.db.collection(Config.USERS_COLLECTION)
            query = users_ref.where(filter=FieldFilter('is_premium', '==', True))
            premium_users = list(query.stream())
            return len(premium_users)
            
        except Exception as e:
            logger.error(f"❌ Error getting premium count: {e}")
            return 0
    
    def get_total_bypasses(self) -> int:
        """Get total bypass count"""
        try:
            users_ref = self.db.collection(Config.USERS_COLLECTION)
            users = users_ref.stream()
            
            total = 0
            for user in users:
                user_data = user.to_dict()
                total += user_data.get('bypass_count', 0)
            
            return total
            
        except Exception as e:
            logger.error(f"❌ Error getting bypass count: {e}")
            return 0
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for broadcasting"""
        try:
            users_ref = self.db.collection(Config.USERS_COLLECTION)
            users = users_ref.stream()
            
            return [user.to_dict() for user in users]
            
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    # Reset Key Operations
    def create_reset_key(self, key_data: Dict[str, Any]) -> bool:
        """Create universal reset key"""
        try:
            key = key_data.get('key')
            key_ref = self.db.collection('reset_keys').document(key)
            
            key_data.setdefault('created_at', firestore.SERVER_TIMESTAMP)
            key_data.setdefault('is_active', True)
            key_data.setdefault('usage_count', 0)
            
            key_ref.set(key_data)
            logger.info(f"✅ Reset key created: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating reset key: {e}")
            return False
    
    def get_reset_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get reset key"""
        try:
            key_ref = self.db.collection('reset_keys').document(key)
            key_doc = key_ref.get()
            
            if key_doc.exists:
                return key_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting reset key: {e}")
            return None
    
    def use_reset_key(self, key: str) -> bool:
        """Increment reset key usage"""
        try:
            key_ref = self.db.collection('reset_keys').document(key)
            
            key_ref.update({
                'usage_count': firestore.Increment(1),
                'last_used': firestore.SERVER_TIMESTAMP
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error using reset key: {e}")
            return False


# Create global database instance
db = FirebaseDB()
