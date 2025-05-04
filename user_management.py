#!/usr/bin/env python3
import os
import json
import hashlib
import time
from pathlib import Path

class UserManager:
    def __init__(self, base_dir="var"):
        self.base_dir = base_dir
        self.users_dir = os.path.join(base_dir, "users")
        self.ensure_dirs_exist()
        self.current_user = None
    
    def ensure_dirs_exist(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.users_dir, exist_ok=True)
    
    def user_exists(self, username):
        """Check if user exists"""
        user_file = os.path.join(self.users_dir, f"{username}.json")
        return os.path.exists(user_file)
    
    def hash_password(self, password):
        """Create secure hash of password"""
        salt = "netapp_secure_salt"  # In production, use a proper salt strategy
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def register_user(self, username, password, ip, port):
        """Register a new user"""
        if self.user_exists(username):
            return False, "Username already exists"
        
        # Create user object
        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "ip": ip,
            "port": port,
            "created_at": time.time(),
            "last_login": None
        }
        
        # Save user to file
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'w') as f:
            json.dump(user_data, f)
        
        return True, "User registered successfully"
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        if not self.user_exists(username):
            return False, "User does not exist"
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        if user_data["password_hash"] == self.hash_password(password):
            # Update last login time
            user_data["last_login"] = time.time()
            with open(user_file, 'w') as f:
                json.dump(user_data, f)
            
            self.current_user = user_data
            return True, "Authentication successful"
        
        return False, "Invalid password"
    
    def get_user_info(self, username):
        """Get user information"""
        if not self.user_exists(username):
            return None
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'r') as f:
            return json.load(f)
    
    def update_user_address(self, username, ip, port):
        """Update user's IP and port"""
        if not self.user_exists(username):
            return False, "User does not exist"
        
        user_data = self.get_user_info(username)
        user_data["ip"] = ip
        user_data["port"] = port
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'w') as f:
            json.dump(user_data, f)
        
        if self.current_user and self.current_user["username"] == username:
            self.current_user = user_data
        
        return True, "User address updated"
    
    def get_current_user(self):
        """Get current logged in user"""
        return self.current_user
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        return True, "Logged out successfully"
    
    def get_all_users(self):
        """Get list of all registered users"""
        users = []
        for filename in os.listdir(self.users_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.users_dir, filename), 'r') as f:
                    user_data = json.load(f)
                    # Don't include password hash in the list
                    users.append({
                        "username": user_data["username"],
                        "ip": user_data["ip"],
                        "port": user_data["port"],
                        "last_login": user_data["last_login"]
                    })
        return users