#!/usr/bin/env python3
"""
RAG Chatbot Setup Script
This script helps you set up the environment for the RAG Chatbot.
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_node_version():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} detected")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org/")
    return False

def create_env_file():
    """Create .env file from env.example if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if not os.path.exists('env.example'):
        print("❌ env.example file not found")
        return False
    
    shutil.copy('env.example', '.env')
    print("✅ Created .env file from env.example")
    print("📝 Please edit .env file and add your API keys:")
    print("   - OPENAI_API_KEY (required)")
    print("   - TAVILY_API_KEY (optional for web search)")
    return True

def setup_backend():
    """Set up the backend environment"""
    print("\n🔧 Setting up backend...")
    
    # Create virtual environment
    if not os.path.exists('env'):
        print("Creating Python virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'env'], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = os.path.join('env', 'Scripts', 'activate.bat')
        pip_path = os.path.join('env', 'Scripts', 'pip.exe')
    else:  # Unix/Linux/macOS
        activate_script = os.path.join('env', 'bin', 'activate')
        pip_path = os.path.join('env', 'bin', 'pip')
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    try:
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Backend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install backend dependencies")
        return False

def setup_frontend():
    """Set up the frontend environment"""
    print("\n🎨 Setting up frontend...")
    
    if not os.path.exists('frontend'):
        print("❌ Frontend directory not found")
        return False
    
    # Install npm dependencies
    try:
        subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        print("✅ Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install frontend dependencies")
        return False

def print_next_steps():
    """Print instructions for next steps"""
    print("\n🎉 Setup complete! Next steps:")
    print("\n1. Configure your API keys in .env file:")
    print("   - Edit .env file")
    print("   - Add your OPENAI_API_KEY (required)")
    print("   - Add your TAVILY_API_KEY (optional)")
    
    print("\n2. Start the backend server:")
    if os.name == 'nt':  # Windows
        print("   env\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source env/bin/activate")
    print("   cd backend")
    print("   python main.py")
    
    print("\n3. Start the frontend server (in a new terminal):")
    print("   cd frontend")
    print("   npm run serve")
    
    print("\n4. Open your browser and go to:")
    print("   http://localhost:8080")
    
    print("\n📚 For more information, see README.md")

def main():
    """Main setup function"""
    print("🚀 RAG Chatbot Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        sys.exit(1)
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main() 