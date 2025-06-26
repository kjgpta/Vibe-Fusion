#!/usr/bin/env python3
"""
Main run script for the Vibe-to-Attribute Clothing Recommendation System

This script:
1. Sets up the environment
2. Creates the sample product catalog
3. Downloads required models
4. Starts the Streamlit application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🌟 Vibe-to-Attribute Clothing Recommendation System 🌟             ║
║                                                                              ║
║  Transform your style ideas into perfect outfit recommendations using AI!    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible."""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"❌ Python {min_version[0]}.{min_version[1]}+ is required. Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    print(f"✅ Python version: {current_version[0]}.{current_version[1]}")
    return True

def install_requirements():
    """Install required Python packages."""
    print("\n📦 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def download_spacy_model():
    """Download required spaCy model."""
    print("\n🤖 Downloading spaCy English model...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "spacy", "download", "en_core_web_md"
        ])
        print("✅ spaCy model downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download spaCy model: {e}")
        print("You can manually install it later with: python -m spacy download en_core_web_md")
        return False

def create_sample_catalog():
    """Create the sample product catalog."""
    print("\n📊 Creating sample product catalog...")
    
    try:
        # Run the catalog creation script
        exec(open('create_catalog.py').read())
        print("✅ Sample catalog created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create sample catalog: {e}")
        return False

def check_environment():
    """Check if environment file exists and provide guidance."""
    print("\n🔧 Checking environment configuration...")
    
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  No .env file found. Please:")
            print("   1. Copy env.example to .env")
            print("   2. Edit .env with your API keys")
            print("   3. Set your OpenAI API key for GPT features")
            print("\n   Example:")
            print("   cp env.example .env")
            print("   # Then edit .env with your actual API keys")
        else:
            print("⚠️  No environment configuration found.")
        
        print("\n💡 The system will work with limited functionality without API keys.")
        print("   GPT inference will be disabled, but rule-based matching will work.")
        return False
    else:
        print("✅ Environment file found!")
        return True

def start_streamlit():
    """Start the Streamlit application."""
    print("\n🚀 Starting Streamlit application...")
    print("📍 The app will open in your default web browser")
    print("🔗 URL: http://localhost:8501")
    print("\n⏹️  Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

def main():
    """Main execution function."""
    print_banner()
    
    print("🔍 System Check...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    print("✅ In correct directory")
    
    # Install requirements
    if not install_requirements():
        print("⚠️  Continuing with existing packages...")
    
    # Download spaCy model
    download_spacy_model()
    
    # Create sample catalog
    create_sample_catalog()
    
    # Check environment
    check_environment()
    
    print("\n" + "="*80)
    print("🎉 Setup complete! Starting the application...")
    print("="*80)
    
    # Start Streamlit
    start_streamlit()

if __name__ == "__main__":
    main() 