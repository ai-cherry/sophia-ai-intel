import asyncio
import json
import os
from typing import Dict, List, Any
from pathlib import Path
from mcp import server, types
from mcp.server import Server
from mcp.server.models import InitializationOptions
import sqlite3
import hashlib
from datetime import datetime

class SophiaContextServer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.server = Server("sophia-context")
        self.db_path = self.repo_path / ".sophia" / "context.db"
        self.dashboard_state = {}
        self.file_index = {}
        self.agent_contexts = {}
        
        # Ensure .sophia directory exists
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.init_database()
        self.setup_handlers()
    
    def init_database(self):
        """Initialize context database"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY,
                content_hash TEXT,
                last_modified TIMESTAMP,
                file_type TEXT,
                size INTEGER,
                indexed_content TEXT
            );
            
            CREATE TABLE IF NOT EXISTS dashboard_context (
                component TEXT PRIMARY KEY,
                state TEXT,
                last_updated TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id TEXT PRIMARY KEY,
                agent_type TEXT,
                context TEXT,
                created_at TIMESTAMP,
                last_active TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS code_dependencies (
                file_path TEXT,
                dependency_path TEXT,
                dependency_type TEXT,
                PRIMARY KEY (file_path, dependency_path)
            );
        """)
        conn.commit()
        conn.close()
    
    def setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="get_repository_context",
                    description="Get complete repository structure and context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Specific path to analyze"}
                        }
                    }
                ),
                types.Tool(
                    name="get_dashboard_state",
                    description="Get current dashboard state and user interactions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {"type": "string", "description": "Specific component state"}
                        }
                    }
                ),
                types.Tool(
                    name="search_codebase",
                    description="Search through indexed codebase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "file_types": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="update_agent_context",
                    description="Update agent context and memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string"},
                            "context": {"type": "object"},
                            "session_data": {"type": "object"}
                        },
                        "required": ["agent_id", "context"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            if name == "get_repository_context":
                return await self.get_repository_context(arguments)
            elif name == "get_dashboard_state":
                return await self.get_dashboard_state(arguments)
            elif name == "search_codebase":
                return await self.search_codebase(arguments)
            elif name == "update_agent_context":
                return await self.update_agent_context(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def get_repository_context(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get repository context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        path = arguments.get("path", "")
        
        if path:
            cursor.execute("SELECT * FROM file_index WHERE path = ?", (path,))
        else:
            cursor.execute("SELECT path, file_type, size FROM file_index LIMIT 100")
        
        results = cursor.fetchall()
        conn.close()
        
        context_text = f"Repository contains {len(results)} indexed files.\n"
        for row in results:
            context_text += f"- {row[0]}\n"
        
        return [types.TextContent(type="text", text=context_text)]
    
    async def get_dashboard_state(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get dashboard state"""
        component = arguments.get("component", "all")
        
        if component == "all":
            return [types.TextContent(type="text", text=json.dumps(self.dashboard_state, indent=2))]
        elif component in self.dashboard_state:
            return [types.TextContent(type="text", text=json.dumps(self.dashboard_state[component], indent=2))]
        else:
            return [types.TextContent(type="text", text=f"No state found for component: {component}")]
    
    async def search_codebase(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Search through codebase"""
        query = arguments.get("query", "")
        file_types = arguments.get("file_types", [])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT path, indexed_content FROM file_index WHERE indexed_content LIKE ?"
        params = [f"%{query}%"]
        
        if file_types:
            placeholders = ",".join("?" * len(file_types))
            sql += f" AND file_type IN ({placeholders})"
            params.extend(file_types)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        search_results = f"Found {len(results)} matches for '{query}':\n"
        for path, content in results[:10]:  # Limit to 10 results
            search_results += f"\n{path}:\n{content[:200]}...\n"
        
        return [types.TextContent(type="text", text=search_results)]
    
    async def update_agent_context(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Update agent context"""
        agent_id = arguments.get("agent_id")
        context = arguments.get("context", {})
        session_data = arguments.get("session_data", {})
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO agent_sessions 
            (session_id, agent_type, context, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_data.get("session_id", agent_id),
            agent_id,
            json.dumps(context),
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        self.agent_contexts[agent_id] = context
        
        return [types.TextContent(type="text", text=f"Context updated for agent: {agent_id}")]
    
    async def index_repository(self):
        """Full repository indexing with dependency tracking"""
        print("🔍 Indexing repository...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and not self.should_ignore_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Check if file changed
                    cursor.execute(
                        "SELECT content_hash FROM file_index WHERE path = ?",
                        (str(file_path.relative_to(self.repo_path)),)
                    )
                    
                    row = cursor.fetchone()
                    if row and row[0] == content_hash:
                        continue  # File hasn't changed
                    
                    # Index file
                    indexed_content = self.extract_searchable_content(file_path, content)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO file_index 
                        (path, content_hash, last_modified, file_type, size, indexed_content)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(file_path.relative_to(self.repo_path)),
                        content_hash,
                        datetime.fromtimestamp(file_path.stat().st_mtime),
                        file_path.suffix,
                        file_path.stat().st_size,
                        indexed_content
                    ))
                    
                    # Extract dependencies
                    dependencies = self.extract_dependencies(file_path, content)
                    cursor.execute(
                        "DELETE FROM code_dependencies WHERE file_path = ?",
                        (str(file_path.relative_to(self.repo_path)),)
                    )
                    
                    for dep in dependencies:
                        cursor.execute("""
                            INSERT INTO code_dependencies (file_path, dependency_path, dependency_type)
                            VALUES (?, ?, ?)
                        """, (
                            str(file_path.relative_to(self.repo_path)),
                            dep['path'],
                            dep['type']
                        ))
                    
                    print(f"📁 Indexed: {file_path.relative_to(self.repo_path)}")
                    
                except Exception as e:
                    print(f"❌ Error indexing {file_path}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Repository indexing complete!")
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during indexing"""
        ignore_patterns = [
            '.git', 'node_modules', '__pycache__', '.next', 'dist', 'build',
            '.DS_Store', '.env', '*.log', '*.tmp', '*.cache'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def extract_searchable_content(self, file_path: Path, content: str) -> str:
        """Extract searchable content from file"""
        if file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
            # Extract function/class names, comments, docstrings
            lines = content.split('\n')
            searchable_lines = []
            
            for line in lines:
                line = line.strip()
                if (line.startswith('#') or line.startswith('//') or 
                    line.startswith('"""') or line.startswith("'''") or
                    'def ' in line or 'class ' in line or 'function ' in line or
                    'const ' in line or 'let ' in line or 'var ' in line):
                    searchable_lines.append(line)
            
            return '\n'.join(searchable_lines)
        
        return content[:1000]  # First 1000 chars for other files
    
    def extract_dependencies(self, file_path: Path, content: str) -> List[Dict[str, str]]:
        """Extract file dependencies"""
        dependencies = []
        
        if file_path.suffix == '.py':
            import re
            # Python imports
            import_patterns = [
                r'from\s+([^\s]+)\s+import',
                r'import\s+([^\s,]+)',
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    dependencies.append({
                        'path': match.strip(),
                        'type': 'python_import'
                    })
        
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            import re
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)',
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    dependencies.append({
                        'path': match.strip(),
                        'type': 'js_import'
                    })
        
        return dependencies
    
    async def update_dashboard_context(self, component: str, state: Dict[str, Any]):
        """Update dashboard component state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_context (component, state, last_updated)
            VALUES (?, ?, ?)
        """, (component, json.dumps(state), datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Also update in-memory state
        self.dashboard_state[component] = state
        
        print(f"🎛️ Updated dashboard context for: {component}")