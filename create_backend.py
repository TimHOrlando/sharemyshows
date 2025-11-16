#!/usr/bin/env python3
"""
ShareMyShows Backend File Generator
Run this to create all backend files automatically
"""
import os

def create_file(path, content):
    """Create a file with given content"""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"✓ Created: {path}")

def main():
    print("🎸 ShareMyShows Backend File Generator")
    print("=" * 50)
    print()
    
    # Create directories
    dirs = [
        'app/models',
        'app/routes', 
        'config',
        'uploads/photos',
        'uploads/audio'
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✓ Created directory structure")
    print()
    
    # Create .gitkeep files
    create_file('uploads/photos/.gitkeep', '')
    create_file('uploads/audio/.gitkeep', '')
    
    # Create __init__.py files
    create_file('config/__init__.py', '# Config package\n')
    create_file('app/routes/__init__.py', '# Routes package\n')
    
    print()
    print("=" * 50)
    print("✅ Basic structure created!")
    print()
    print("Next steps:")
    print("1. I'll give you the remaining files in separate messages")
    print("2. Or run the detailed setup commands")
    print()

if __name__ == '__main__':
    main()
