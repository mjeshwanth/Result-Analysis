#!/usr/bin/env python3
"""
Create Admin User for Firebase Authentication
"""

import firebase_admin
from firebase_admin import auth, credentials

def create_admin_user():
    """Create an admin user in Firebase Authentication"""
    
    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccount.json')
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase initialized")
        
        # Create admin user
        admin_email = "admin@scrreddy.edu.in"
        admin_password = "admin123456"  # Change this to a secure password
        
        user = auth.create_user(
            email=admin_email,
            password=admin_password,
            display_name="System Administrator"
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"🆔 User ID: {user.uid}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        
    except auth.EmailAlreadyExistsError:
        print("✅ Admin user already exists!")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()
