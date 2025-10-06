#!/usr/bin/env python3
"""
Student Services Platform - Admin User Creation Script
Create admin user with hashed password
"""

import sys
import os
from pathlib import Path
import getpass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from passlib.context import CryptContext

def main():
    """
    Create admin user with secure password hash
    """
    print("Student Services Platform - Admin User Creation")
    print("=" * 50)
    
    # Initialize password context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Get admin credentials
    print("\nEnter admin credentials:")
    username = input("Username [admin]: ").strip() or "admin"
    
    while True:
        password = getpass.getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters long!")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords don't match!")
            continue
        
        break
    
    # Generate password hash
    password_hash = pwd_context.hash(password)
    
    print(f"\nAdmin credentials generated:")
    print(f"Username: {username}")
    print(f"Password Hash: {password_hash}")
    
    # Update .env file
    env_file = project_root / ".env"
    
    if env_file.exists():
        print(f"\nUpdating {env_file}...")
        
        # Read current .env content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add admin settings
        updated_lines = []
        admin_username_set = False
        admin_password_hash_set = False
        
        for line in lines:
            if line.startswith('ADMIN_USERNAME=') or line.startswith('admin_username='):
                updated_lines.append(f"ADMIN_USERNAME={username}\n")
                updated_lines.append(f"admin_username={username}\n")
                admin_username_set = True
            elif line.startswith('ADMIN_PASSWORD_HASH=') or line.startswith('admin_password_hash='):
                updated_lines.append(f"ADMIN_PASSWORD_HASH={password_hash}\n")
                updated_lines.append(f"admin_password_hash={password_hash}\n")
                admin_password_hash_set = True
            elif not line.startswith('ADMIN_PASSWORD=') and not line.startswith('admin_password='):
                # Skip plain password lines for security
                updated_lines.append(line)
        
        # Add admin settings if not present
        if not admin_username_set:
            updated_lines.append(f"\n# Admin Authentication\n")
            updated_lines.append(f"ADMIN_USERNAME={username}\n")
            updated_lines.append(f"admin_username={username}\n")
        
        if not admin_password_hash_set:
            updated_lines.append(f"ADMIN_PASSWORD_HASH={password_hash}\n")
            updated_lines.append(f"admin_password_hash={password_hash}\n")
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
    else:
        print(f"\n⚠️  .env file not found at {env_file}")
        print("Please add these lines to your .env file:")
        print(f"ADMIN_USERNAME={username}")
        print(f"admin_username={username}")
        print(f"ADMIN_PASSWORD_HASH={password_hash}")
        print(f"admin_password_hash={password_hash}")
    
    print("\n🔐 Security Notes:")
    print("1. The password hash has been generated using bcrypt")
    print("2. The plain text password is not stored anywhere")
    print("3. Make sure to keep your .env file secure")
    print("4. Consider using environment variables in production")
    
    print(f"\n✅ Admin user '{username}' created successfully!")
    print("You can now log in to the admin panel with these credentials.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
