#!/usr/bin/env python
"""
CIHRPT Development Server Starter
Makes it easy to start the Django development server with environment configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the Django development server with environment configuration."""
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🚀 CIHRPT Development Server Starter")
    print("=" * 50)
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  No .env file found!")
        print("📝 Creating .env file with default settings...")
        
        # Create default .env file
        env_content = """# Django Configuration
SECRET_KEY=django-insecure-your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,cihrpt.xeradb.com

# Server Configuration - Change these ports as needed!
PORT=8000
HOST=127.0.0.1

# Alternative ports you might want to use:
# PORT=8001  # For development instance 2
# PORT=8002  # For testing
# PORT=8080  # Common alternative
# PORT=3000  # If you prefer Node.js style
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default settings")
        print()
    
    # Show current configuration
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'runserver_env', '--show-config'
        ], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return 1
    
    # Ask user what they want to do
    print("🎯 What would you like to do?")
    print("1. Start server with current settings")
    print("2. Start server with different port")
    print("3. Edit .env file")
    print("4. Exit")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == '1':
        # Start with current settings
        subprocess.run([sys.executable, 'manage.py', 'runserver_env'])
    
    elif choice == '2':
        # Start with custom port
        port = input("Enter port number: ").strip()
        try:
            port = int(port)
            subprocess.run([sys.executable, 'manage.py', 'runserver_env', '--port', str(port)])
        except ValueError:
            print("❌ Invalid port number")
            return 1
    
    elif choice == '3':
        # Edit .env file
        print("📝 Opening .env file...")
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', '-e', '.env'])
        elif sys.platform == 'linux':
            subprocess.run(['nano', '.env'])
        elif sys.platform == 'win32':
            subprocess.run(['notepad', '.env'])
        else:
            print("Please manually edit the .env file")
    
    elif choice == '4':
        print("👋 Goodbye!")
        return 0
    
    else:
        print("❌ Invalid choice")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 