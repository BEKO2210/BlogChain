import os
import json
import time
import base64
import uuid
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.encryption import (
    generate_key_pair, 
    generate_signing_key_pair,
    derive_key_from_password,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature
)
from utils.logger import get_logger

logger = get_logger(__name__)

class User:
    """User model for the BlockJournal platform."""
    
    def __init__(self, username, user_id=None, profile=None):
        """
        Initialize a new or existing user.
        
        Args:
            username (str): User's chosen username
            user_id (str, optional): Unique identifier for the user
            profile (dict, optional): User profile data
        """
        self.username = username
        self.user_id = user_id or str(uuid.uuid4())
        self.profile = profile or {}
        self.created_at = int(time.time())
        self.last_active = int(time.time())
        self.private_key = None
        self.public_key = None
        self.signing_key = None
        self.verify_key = None
        self.encryption_key = None
        self.salt = None
        self.is_authenticated = False
        self.session_expires = 0
        self.settings = {
            "mining_difficulty": 4,
            "session_timeout": 30,  # minutes
            "theme": "light",
            "auto_sync": False,
            "log_level": "INFO"
        }
        
        logger.info(f"User object initialized for {username} (ID: {self.user_id})")
    
    def generate_keys(self, password):
        """
        Generate cryptographic keys for the user.
        
        Args:
            password (str): User's password for key derivation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate encryption key from password
            self.encryption_key, self.salt = derive_key_from_password(password)
            
            # Generate asymmetric key pair
            self.private_key, self.public_key = generate_key_pair()
            
            # Generate signing key pair
            self.signing_key, self.verify_key = generate_signing_key_pair()
            
            logger.info(f"Cryptographic keys generated for user {self.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate keys: {str(e)}")
            return False
    
    def authenticate(self, password):
        """
        Authenticate the user with their password.
        
        Args:
            password (str): User's password
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if not self.salt:
            logger.error("Cannot authenticate: salt not available")
            return False
        
        try:
            # Derive key from provided password and stored salt
            derived_key, _ = derive_key_from_password(password, self.salt)
            
            # Check if the derived key matches the stored encryption key
            if derived_key == self.encryption_key:
                self.is_authenticated = True
                self.last_active = int(time.time())
                self.session_expires = int(time.time()) + (self.settings["session_timeout"] * 60)
                logger.info(f"User {self.username} authenticated successfully")
                return True
            else:
                logger.warning(f"Authentication failed for user {self.username}: incorrect password")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def check_session(self):
        """
        Check if the user's session is still valid.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        current_time = int(time.time())
        
        if not self.is_authenticated:
            return False
        
        if current_time > self.session_expires:
            self.is_authenticated = False
            logger.info(f"Session expired for user {self.username}")
            return False
        
        # Extend session on activity
        self.last_active = current_time
        self.session_expires = current_time + (self.settings["session_timeout"] * 60)
        return True
    
    def logout(self):
        """Log out the user by invalidating their session."""
        self.is_authenticated = False
        self.session_expires = 0
        logger.info(f"User {self.username} logged out")
    
    def update_profile(self, profile_data, password=None):
        """
        Update the user's profile.
        
        Args:
            profile_data (dict): New profile data
            password (str, optional): User's password if changing sensitive data
            
        Returns:
            bool: True if successful, False otherwise
        """
        # For sensitive updates, verify password
        sensitive_fields = ["email", "password"]
        requires_password = any(field in profile_data for field in sensitive_fields)
        
        if requires_password:
            if not password or not self.authenticate(password):
                logger.warning(f"Profile update failed: password verification failed")
                return False
        
        try:
            # Update profile
            for key, value in profile_data.items():
                if key == "password":
                    # Handle password change
                    self.encryption_key, self.salt = derive_key_from_password(value)
                else:
                    # Update regular profile field
                    self.profile[key] = value
            
            logger.info(f"Profile updated for user {self.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to update profile: {str(e)}")
            return False
    
    def update_settings(self, new_settings):
        """
        Update user settings.
        
        Args:
            new_settings (dict): New settings values
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for key, value in new_settings.items():
                if key in self.settings:
                    # Validate settings where necessary
                    if key == "mining_difficulty" and value < 1:
                        value = 1
                    elif key == "session_timeout" and value < 1:
                        value = 1
                    
                    self.settings[key] = value
            
            logger.info(f"Settings updated for user {self.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to update settings: {str(e)}")
            return False
    
    def to_dict(self, include_keys=False):
        """
        Convert user object to dictionary for serialization.
        
        Args:
            include_keys (bool): Whether to include cryptographic keys
            
        Returns:
            dict: User data as dictionary
        """
        user_data = {
            "username": self.username,
            "user_id": self.user_id,
            "profile": self.profile,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "settings": self.settings
        }
        
        if include_keys and self.private_key and self.public_key:
            user_data["keys"] = {
                "public_key": base64.b64encode(self.public_key).decode(),
                "verify_key": base64.b64encode(self.verify_key).decode(),
                "salt": base64.b64encode(self.salt).decode()
            }
            
            # Encrypt sensitive keys with the encryption key
            encrypted_keys = {
                "private_key": encrypt_data(self.private_key, self.encryption_key),
                "signing_key": encrypt_data(self.signing_key, self.encryption_key)
            }
            user_data["encrypted_keys"] = encrypted_keys
        
        return user_data
    
    @classmethod
    def from_dict(cls, data, password=None):
        """
        Create a User instance from a dictionary.
        
        Args:
            data (dict): User data
            password (str, optional): Password to decrypt keys
            
        Returns:
            User: User object
        """
        user = cls(data["username"], data["user_id"], data["profile"])
        user.created_at = data["created_at"]
        user.last_active = data["last_active"]
        user.settings = data["settings"]
        
        # Load keys if available and password provided
        if "keys" in data and "encrypted_keys" in data and password:
            try:
                # Load public keys
                user.public_key = base64.b64decode(data["keys"]["public_key"])
                user.verify_key = base64.b64decode(data["keys"]["verify_key"])
                user.salt = base64.b64decode(data["keys"]["salt"])
                
                # Derive encryption key from password
                user.encryption_key, _ = derive_key_from_password(password, user.salt)
                
                # Decrypt private keys
                user.private_key = decrypt_data(data["encrypted_keys"]["private_key"], user.encryption_key)
                user.signing_key = decrypt_data(data["encrypted_keys"]["signing_key"], user.encryption_key)
                
                user.is_authenticated = True
                user.session_expires = int(time.time()) + (user.settings["session_timeout"] * 60)
                logger.info(f"User {user.username} loaded with keys")
            except Exception as e:
                logger.error(f"Failed to load user keys: {str(e)}")
        
        return user
    
    def save_to_file(self, file_path, include_keys=True):
        """
        Save user data to a file.
        
        Args:
            file_path (str): Path to save the user data
            include_keys (bool): Whether to include cryptographic keys
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user_data = self.to_dict(include_keys)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(user_data, f, indent=4)
            
            logger.info(f"User data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user data: {str(e)}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path, password=None):
        """
        Load user data from a file.
        
        Args:
            file_path (str): Path to the user data file
            password (str, optional): Password to decrypt keys
            
        Returns:
            User: User object or None if loading failed
        """
        try:
            with open(file_path, 'r') as f:
                user_data = json.load(f)
            
            user = cls.from_dict(user_data, password)
            logger.info(f"User data loaded from {file_path}")
            return user
        except Exception as e:
            logger.error(f"Failed to load user data: {str(e)}")
            return None
