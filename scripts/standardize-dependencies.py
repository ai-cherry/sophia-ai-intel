#!/usr/bin/env python3
"""
Dependency Standardization Script
Analyzes and standardizes dependencies across all services to prevent version conflicts
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import subprocess

class DependencyStandardizer:
    """Standardizes dependencies across all services"""
    
    def __init__(self):
        self.dependency_files = []
        self.all_dependencies = defaultdict(list)
        self.conflicts = {}
        self.standardized_versions = {}
        
    def find_all_requirement_files(self) -> List[Path]:
        """Find all requirements.txt and pyproject.toml files"""
        req_files = []
        
        # Find requirements.txt files
        for req_file in Path('.').glob('**/requirements.txt'):
            if 'node_modules' not in str(req_file) and '.git' not in str(req_file):
                req_files.append(req_file)
        
        # Find pyproject.toml files  
        for toml_file in Path('.').glob('**/pyproject.toml'):
            if 'node_modules' not in str(toml_file) and '.git' not in str(toml_file):
                req_files.append(toml_file)
                
        return sorted(req_files)
    
    def parse_requirements_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Parse requirements file and extract package versions"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            if file_path.name == 'requirements.txt':
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name and version
                        if '>=' in line:
                            parts = line.split('>=')
                            package = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else ''
                        elif '==' in line:
                            parts = line.split('==')
                            package = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else ''
                        elif '~=' in line:
                            parts = line.split('~=')
                            package = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else ''
                        else:
                            package = line.strip()
                            version = 'unspecified'
                        
                        dependencies.append((package, version))
                        
            elif file_path.name == 'pyproject.toml':
                # Extract from [tool.poetry.dependencies] section
                in_dependencies = False
                for line in content.split('\n'):
                    line = line.strip()
                    if '[tool.poetry.dependencies]' in line:
                        in_dependencies = True
                        continue
                    if in_dependencies and line.startswith('['):
                        break
                    if in_dependencies and '=' in line and not line.startswith('#'):
                        parts = line.split('=')
                        package = parts[0].strip()
                        version = parts[1].strip().strip('"\'') if len(parts) > 1 else ''
                        dependencies.append((package, version))
                        
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            
        return dependencies
    
    def analyze_dependencies(self):
        """Analyze all dependencies and identify conflicts"""
        print("🔍 Analyzing dependency files...")
        
        self.dependency_files = self.find_all_requirement_files()
        print(f"Found {len(self.dependency_files)} dependency files")
        
        # Parse all files
        for file_path in self.dependency_files:
            print(f"  📄 Analyzing: {file_path}")
            deps = self.parse_requirements_file(file_path)
            
            for package, version in deps:
                self.all_dependencies[package].append({
                    'file': str(file_path),
                    'version': version
                })
        
        # Identify conflicts
        print("\n🔍 Identifying version conflicts...")
        for package, versions in self.all_dependencies.items():
            unique_versions = set(v['version'] for v in versions if v['version'] != 'unspecified')
            if len(unique_versions) > 1:
                self.conflicts[package] = versions
                print(f"  ⚠️  {package}: {unique_versions}")
    
    def get_latest_stable_version(self, package_name: str) -> str:
        """Get latest stable version from PyPI (simplified approach)"""
        # For critical packages, use known stable versions
        stable_versions = {
            'fastapi': '0.111.1',
            'uvicorn': '0.30.1', 
            'pydantic': '2.8.2',
            'openai': '1.12.0',
            'anthropic': '0.34.0',
            'redis': '5.0.8',
            'psycopg2-binary': '2.9.9',
            'sqlalchemy': '2.0.35',
            'qdrant-client': '1.10.1',
            'requests': '2.32.3',
            'aiohttp': '3.10.5',
            'pytest': '8.3.2',
            'pytest-asyncio': '0.23.8',
            'python-multipart': '0.0.9',
            'python-dotenv': '1.0.1',
            'cryptography': '43.0.0',
            'pyjwt': '2.9.0',
            'httpx': '0.27.0',
            'structlog': '24.2.0',
            'prometheus-client': '0.20.0',
            'opentelemetry-api': '1.25.0',
            'opentelemetry-sdk': '1.25.0',
            'gunicorn': '22.0.0',
            'celery': '5.3.4',
            'kombu': '5.3.4'
        }
        
        return stable_versions.get(package_name, 'latest')
    
    def create_standardized_requirements(self):
        """Create standardized requirements for all services"""
        print("\n📋 Creating standardized dependency versions...")
        
        # Define standard versions for critical packages
        for package in self.conflicts:
            self.standardized_versions[package] = self.get_latest_stable_version(package)
            print(f"  ✅ {package} -> {self.standardized_versions[package]}")
        
        # Create master requirements file
        master_requirements = """# Sophia AI Platform - Standardized Dependencies
# Generated: 2025-08-27
# All services should use these standardized versions

# =============================================================================
# WEB FRAMEWORK & API
# =============================================================================
fastapi==0.111.1
uvicorn[standard]==0.30.1
pydantic==2.8.2
python-multipart==0.0.9
python-dotenv==1.0.1
gunicorn==22.0.0

# =============================================================================
# HTTP CLIENTS & ASYNC
# =============================================================================
httpx==0.27.0
aiohttp==3.10.5
requests==2.32.3
websockets==12.0

# =============================================================================
# DATABASE & STORAGE
# =============================================================================
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.13.2
redis==5.0.8
qdrant-client==1.10.1

# =============================================================================
# LLM & AI INTEGRATIONS
# =============================================================================
openai==1.12.0
anthropic==0.34.0
portkey-ai==0.1.84
agno==0.1.82

# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================
pyjwt==2.9.0
cryptography==43.0.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# =============================================================================
# MONITORING & OBSERVABILITY
# =============================================================================
prometheus-client==0.20.0
structlog==24.2.0
opentelemetry-api==1.25.0
opentelemetry-sdk==1.25.0
opentelemetry-instrumentation-fastapi==0.46b0
opentelemetry-exporter-prometheus==1.12.0

# =============================================================================
# TASK PROCESSING & QUEUES
# =============================================================================
celery==5.3.4
kombu==5.3.4
flower==2.0.1

# =============================================================================
# TESTING & DEVELOPMENT
# =============================================================================
pytest==8.3.2
pytest-asyncio==0.23.8
pytest-cov==5.0.0

# =============================================================================
# UTILITIES
# =============================================================================
pydantic-settings==2.4.0
python-dateutil==2.9.0
pytz==2024.1
click==8.1.7
rich==13.7.1
typer==0.12.3
jinja2==3.1.4

# =============================================================================
# BUSINESS INTEGRATIONS
# =============================================================================
hubspot-api-client==9.2.0
slack-sdk==3.31.0
salesforce-bulk==2.2.0

# =============================================================================
# RESEARCH & DATA
# =============================================================================
google-search-results==2.4.2
tavily-python==0.3.3
beautifulsoup4==4.12.3
lxml==5.2.2
pandas==2.2.2
numpy==2.0.1

# =============================================================================
# VECTOR & EMBEDDINGS
# =============================================================================
sentence-transformers==3.0.1
transformers==4.44.0
torch==2.4.0
llama-index==0.10.57
llama-index-embeddings-openai==0.1.11
llama-index-vector-stores-qdrant==0.2.8
"""

        with open('requirements-standardized.txt', 'w') as f:
            f.write(master_requirements)
        
        print("✅ Created requirements-standardized.txt")
    
    def run_analysis(self):
        """Run complete dependency analysis"""
        print("🔍 Starting dependency standardization analysis...\n")
        
        self.analyze_dependencies()
        self.create_standardized_requirements()
        
        print(f"\n📊 Analysis Complete:")
        print(f"  📄 Found {len(self.dependency_files)} dependency files")
        print(f"  ⚠️  Identified {len(self.conflicts)} packages with version conflicts")
        print(f"  ✅ Generated standardized requirements")
        
        # Generate conflict report
        if self.conflicts:
            print(f"\n⚠️  CRITICAL CONFLICTS FOUND:")
            for package, versions in list(self.conflicts.items())[:10]:  # Show top 10
                unique_versions = set(v['version'] for v in versions if v['version'] != 'unspecified')
                print(f"    {package}: {unique_versions}")
                for version_info in versions[:3]:  # Show first 3 files
                    print(f"      {version_info['file']}: {version_info['version']}")
        
        return self.conflicts

def main():
    """Main function"""
    standardizer = DependencyStandardizer()
    conflicts = standardizer.run_analysis()
    
    if conflicts:
        print(f"\n🚨 CRITICAL: {len(conflicts)} dependency conflicts detected")
        print("💡 Use requirements-standardized.txt as reference for updates")
        print("💡 Manually update each service's requirements.txt file")
    else:
        print("\n✅ No dependency conflicts detected")

if __name__ == "__main__":
    main()
