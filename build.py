#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OrrerySQL Build Script
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_directories():
    """Clean previous build artifacts."""
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def install_dependencies():
    """Install required packages."""
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)

def build_executable():
    """Build executable using PyInstaller."""
    print("🔨 Building executable with PyInstaller...")
    subprocess.run([sys.executable, '-m', 'PyInstaller', 'OrrerySQL.spec'], check=True)
    
def check_build():
    """Check if build was successful."""
    exe_path = Path('dist/OrrerySQL.exe')
    if exe_path.exists():
        print(f"✅ Build successful! Executable created at: {exe_path}")
        print(f"📊 File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        return True
    else:
        print("❌ Build failed! Executable not found.")
        return False

def main():
    """Main build process."""
    print("🚀 Starting OrrerySQL build process...")
    
    try:
        # Step 1: Clean
        clean_build_directories()
        
        # Step 2: Install dependencies
        install_dependencies()
        
        # Step 3: Build
        build_executable()
        
        # Step 4: Check
        if check_build():
            print("🎉 Build completed successfully!")
            print("💡 You can now run: ./dist/OrrerySQL.exe")
        else:
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 