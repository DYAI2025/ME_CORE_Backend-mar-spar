#!/usr/bin/env python3
"""
TransRapport Desktop MVP Implementation Validation

Validates that all required components are in place and correctly configured.
"""

import os
import yaml
import json
from pathlib import Path

def check_file(path, description):
    """Check if a file exists and is readable"""
    if Path(path).exists():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description}: {path} (missing)")
        return False

def check_yaml_config(path, description):
    """Check if YAML config is valid"""
    if not Path(path).exists():
        print(f"✗ {description}: {path} (missing)")
        return False
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        print(f"✓ {description}: {path} (valid YAML)")
        return True
    except Exception as e:
        print(f"✗ {description}: {path} (invalid YAML: {e})")
        return False

def main():
    """Validate TransRapport Desktop MVP implementation"""
    print("TransRapport Desktop MVP - Implementation Validation")
    print("=" * 55)
    
    # Check core configuration files
    print("\n📁 Configuration Files:")
    config_ok = check_yaml_config("config/app.yaml", "Main Configuration")
    bundle_ok = check_yaml_config("bundles/SerapiCore_1.0.yaml", "Marker Bundle")
    
    # Check core backend files
    print("\n🚀 Backend Components:")
    backend_files = [
        ("backend/main.py", "Main Server Entry Point"),
        ("backend/app_config.py", "Configuration Loader"),
        ("backend/realtime_marker_engine.py", "Real-time Marker Engine"),
        ("backend/api/dashboard.py", "WebSocket API"),
    ]
    
    backend_ok = all(check_file(path, desc) for path, desc in backend_files)
    
    # Check tools and scripts
    print("\n🔧 Tools & Scripts:")
    tool_files = [
        ("tools/mic_ws_sender.py", "Audio Capture Tool"),
        ("Makefile", "Build System"),
        ("demo_transrapport.py", "Interactive Demo"),
        ("test_websockets.py", "WebSocket Tests"),
        ("TRANSRAPPORT_README.md", "Documentation"),
    ]
    
    tools_ok = all(check_file(path, desc) for path, desc in tool_files)
    
    # Check directory structure
    print("\n📂 Directory Structure:")
    directories = [
        ("config", "Configuration Directory"),
        ("bundles", "Marker Bundles Directory"),
        ("backend", "Backend Source"),
        ("backend/api", "API Endpoints"),
        ("tools", "Tools Directory"),
    ]
    
    dirs_ok = all(check_file(path, desc) for path, desc in directories)
    
    # Validate configuration contents
    print("\n⚙️ Configuration Validation:")
    if config_ok:
        try:
            with open("config/app.yaml", 'r') as f:
                config = yaml.safe_load(f)
            
            # Check key sections
            required_sections = ['server', 'markers', 'audio', 'events', 'offline']
            sections_ok = True
            for section in required_sections:
                if section in config:
                    print(f"✓ Config section: {section}")
                else:
                    print(f"✗ Config section: {section} (missing)")
                    sections_ok = False
            
            # Check server port
            server_port = config.get('server', {}).get('port', None)
            if server_port == 8710:
                print(f"✓ Server port: {server_port}")
            else:
                print(f"✗ Server port: expected 8710, got {server_port}")
                sections_ok = False
                
        except Exception as e:
            print(f"✗ Configuration validation failed: {e}")
            sections_ok = False
    else:
        sections_ok = False
    
    # Check marker bundle contents
    print("\n🎯 Marker Bundle Validation:")
    if bundle_ok:
        try:
            with open("bundles/SerapiCore_1.0.yaml", 'r') as f:
                bundle = yaml.safe_load(f)
            
            # Check categories
            categories = bundle.get('categories', {})
            expected_categories = ['ATO', 'SEM', 'CLU', 'INTUITION']
            for cat in expected_categories:
                if cat in categories:
                    print(f"✓ Marker category: {cat}")
                else:
                    print(f"✗ Marker category: {cat} (missing)")
                    bundle_ok = False
                    
        except Exception as e:
            print(f"✗ Bundle validation failed: {e}")
            bundle_ok = False
    
    # Summary
    print("\n📋 Implementation Status:")
    all_components = [
        ("Configuration System", config_ok and sections_ok),
        ("Marker Bundle", bundle_ok),
        ("Backend Components", backend_ok),
        ("Tools & Scripts", tools_ok),
        ("Directory Structure", dirs_ok),
    ]
    
    total_ok = 0
    for component, status in all_components:
        if status:
            print(f"✓ {component}")
            total_ok += 1
        else:
            print(f"✗ {component}")
    
    print(f"\nImplementation Complete: {total_ok}/{len(all_components)} components")
    
    if total_ok == len(all_components):
        print("\n🎉 TransRapport Desktop MVP implementation is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: make deps")
        print("2. Start the server: make run")
        print("3. Access UI: http://127.0.0.1:8710/")
        print("4. Run demo: make demo")
        return True
    else:
        print("\n⚠️  Some components are missing or incomplete.")
        print("Review the validation results above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)