import re
from collections import defaultdict, Counter

file_contents = {
    'mcp/enrichment-mcp/requirements.txt': '''fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0''',
    'mcp/support-mcp/requirements.txt': '''fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0''',
    'services/agno-teams/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/agno-wrappers/requirements.txt': '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.25.2
aiofiles==23.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
requests==2.31.0''',
    'services/mcp-agents/requirements.txt': '''# Sophia AI Agent Swarm MCP Service Dependencies

# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.3

# HTTP client for MCP integration
httpx==0.26.0
aiohttp==3.9.1

# Agent swarm framework dependencies
langgraph==0.2.16
langchain==0.2.16
langchain-core==0.2.40
langchain-community==0.2.17

# PostgreSQL checkpoint dependencies for LangGraph
psycopg2-binary==2.9.9

# Embedding and ML dependencies
sentence-transformers==2.2.2
transformers==4.36.2
torch==2.1.2
numpy==1.24.4
scikit-learn==1.3.2

# Vector database clients
qdrant-client==1.7.0
faiss-cpu==1.7.4

# Text processing
tiktoken==0.5.2

# AST and code analysis
astroid==3.0.3
tree-sitter==0.20.4

# Database and storage
asyncpg==0.29.0
sqlalchemy==2.0.25

# Monitoring and logging
structlog==23.2.0
prometheus-client==0.19.0

# Utilities
ujson==5.9.0
python-dotenv==1.0.0
tenacity==8.2.3

# Development
pytest==7.4.4
pytest-asyncio==0.23.2''',
    'services/mcp-apollo/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/mcp-business/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.2
pydantic==2.8.2
python-dotenv==1.0.1
asyncpg==0.29.0
python-multipart==0.0.9
aiofiles==23.2.1
PyJWT==2.8.0
cryptography==41.0.7''',
    'services/mcp-context/requirements.txt': '''# Sophia AI Context Service Dependencies
# Core MCP service for context management and vector search

# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.3

# Database and storage
asyncpg==0.29.0
sqlalchemy==2.0.25

# Vector database and embeddings
qdrant-client==1.7.0
openai==1.6.1
redis==5.0.1

# Utilities and performance
ujson==5.9.0
python-dotenv==1.0.0
numpy==1.24.4

# HTTP client
httpx==0.26.0

# Logging and monitoring
structlog==23.2.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.2''',
    'services/mcp-github/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.2
pydantic==2.8.2
python-dotenv==1.0.1
PyJWT[crypto]>=2.4.0
cryptography>=3.4.8''',
    'services/mcp-gong/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/mcp-hubspot/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/mcp-lambda/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/mcp-research/requirements.txt': '''# Sophia AI Research Service Dependencies
# Core MCP service for research and data acquisition

# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.3

# Database and storage
asyncpg==0.29.0
sqlalchemy==2.0.25

# HTTP client for external APIs
httpx==0.26.0

# Vector database
qdrant-client==1.7.0

# Redis caching - temporarily disabled aioredis due to Python 3.11 compatibility
redis==5.0.1
# aioredis==2.0.1  # Temporarily disabled - TimeoutError base class conflict

# Utilities
ujson==5.9.0
python-dotenv==1.0.0

# Logging and monitoring
structlog==23.2.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.2''',
    'services/mcp-salesforce/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1''',
    'services/mcp-slack/requirements.txt': '''fastapi==0.111.0
uvicorn[standard]==0.30.1
aiohttp==3.9.5
asyncpg==0.29.0
redis>=5.0.0
pydantic==2.8.2
python-dotenv==1.0.1'''
}

all_packages = defaultdict(set)
package_occurrences = defaultdict(set) # To count distinct services per package
package_version_counts = defaultdict(Counter) # To count occurrences of specific versions

total_services = len(file_contents)

for service_path, content in file_contents.items():
    service_short_name = service_path.split('/')[1]
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        match = re.match(r'^([\w\-\_\[\]]+)(?:([<>=!~]+)(.*))?$', line)
        if match:
            pkg_name_with_extras = match.group(1)
            pkg_name = pkg_name_with_extras.split('[')[0]
            operator = match.group(2)
            version = match.group(3)

            full_spec = line # Store the original line for `all_packages` and `package_version_counts`
            
            all_packages[pkg_name].add(full_spec)
            package_version_counts[pkg_name][full_spec] += 1
            package_occurrences[pkg_name].add(service_short_name)

# --- Analysis ---

# 1. Sorted list of all unique Python packages
unique_packages = sorted(list(all_packages.keys()))

# 2. Identify common packages and their most frequent versions
common_packages_threshold = 8
common_packages_info = {}
inconsistent_versions = {}

for pkg_name in unique_packages:
    if len(package_occurrences[pkg_name]) >= common_packages_threshold:
        most_common_spec = package_version_counts[pkg_name].most_common(1)[0][0]
        
        common_packages_info[pkg_name] = most_common_spec

        if len(all_packages[pkg_name]) > 1:
            inconsistent_versions[pkg_name] = sorted(list(all_packages[pkg_name]))

# Prepare the output
result_str = "Analysis of `requirements.txt` files for common Python dependencies:\n\n"

result_str += "### Sorted List of All Unique Python Packages Found:\n"
for pkg in unique_packages:
    result_str += f"- {pkg}\n"

result_str += "\n### Common Packages and Their Most Frequently Specified Versions (appearing in at least 8 out of 15 services):\n"
if common_packages_info:
    for pkg, version_spec in sorted(common_packages_info.items()):
        result_str += f"- {pkg}: {version_spec}\n"
else:
    result_str += "No packages found to be common across 8 or more services.\n"

result_str += "\n### Inconsistencies in Package Versions for Common Dependencies:\n"
if inconsistent_versions:
    for pkg, versions in sorted(inconsistent_versions.items()):
        result_str += f"- {pkg}: {', '.join(versions)}\n"
else:
    result_str += "No significant version inconsistencies found for common dependencies.\n"

print(result_str)
