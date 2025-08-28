"""
Repository Context Indexer for Sophia AI MCP Context Service

This module provides comprehensive repository indexing capabilities including:
- Full codebase indexing with content extraction
- Dependency tracking and analysis
- Real-time file change detection
- Dashboard state synchronization
- Code search and navigation

Integrates with existing MCP context service for unified context management.
"""

import os
import asyncio
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import re
import ast
from dataclasses import dataclass
from collections import defaultdict

# Import existing MCP components
from real_embeddings import embedding_engine, store_with_real_embedding


@dataclass
class FileIndex:
    """Represents an indexed file with metadata"""
    path: str
    content_hash: str
    last_modified: datetime
    file_type: str
    size: int
    indexed_content: str
    dependencies: List[Dict[str, str]]
    symbols: List[Dict[str, Any]]


class RepositoryIndexer:
    """
    Advanced repository indexer with full context awareness
    """
    
    def __init__(self, repo_path: str, db_path: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.db_path = db_path or (self.repo_path / ".sophia" / "repo_index.db")
        self.file_cache = {}
        self.dependency_graph = defaultdict(list)
        self.symbol_index = {}
        
        # Ensure .sophia directory exists
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize repository index database"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY,
                content_hash TEXT,
                last_modified TIMESTAMP,
                file_type TEXT,
                size INTEGER,
                indexed_content TEXT,
                symbols TEXT,
                embeddings TEXT
            );
            
            CREATE TABLE IF NOT EXISTS dependencies (
                file_path TEXT,
                dependency_path TEXT,
                dependency_type TEXT,
                line_number INTEGER,
                PRIMARY KEY (file_path, dependency_path, line_number)
            );
            
            CREATE TABLE IF NOT EXISTS symbols (
                symbol_name TEXT,
                symbol_type TEXT,
                file_path TEXT,
                line_number INTEGER,
                definition TEXT,
                PRIMARY KEY (symbol_name, file_path, line_number)
            );
            
            CREATE TABLE IF NOT EXISTS dashboard_context (
                component TEXT PRIMARY KEY,
                state TEXT,
                last_updated TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_file_type ON file_index(file_type);
            CREATE INDEX IF NOT EXISTS idx_symbol_type ON symbols(symbol_type);
            CREATE INDEX IF NOT EXISTS idx_dependency_type ON dependencies(dependency_type);
        """)
        conn.commit()
        conn.close()
    
    async def index_repository(self, progress_callback=None):
        """
        Perform complete repository indexing
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        print("🔍 Starting comprehensive repository indexing...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_files = 0
        indexed_files = 0
        errors = []
        
        # Count total files first
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and not self.should_ignore_file(file_path):
                total_files += 1
        
        # Index each file
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and not self.should_ignore_file(file_path):
                try:
                    # Read file content
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Check if file has changed
                    rel_path = str(file_path.relative_to(self.repo_path))
                    cursor.execute(
                        "SELECT content_hash FROM file_index WHERE path = ?",
                        (rel_path,)
                    )
                    
                    row = cursor.fetchone()
                    if row and row[0] == content_hash:
                        indexed_files += 1
                        continue  # File hasn't changed
                    
                    # Extract file information
                    file_info = await self.extract_file_info(file_path, content)
                    
                    # Store in database
                    cursor.execute("""
                        INSERT OR REPLACE INTO file_index 
                        (path, content_hash, last_modified, file_type, size, 
                         indexed_content, symbols, embeddings)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rel_path,
                        content_hash,
                        datetime.fromtimestamp(file_path.stat().st_mtime),
                        file_path.suffix,
                        file_path.stat().st_size,
                        file_info['indexed_content'],
                        json.dumps(file_info['symbols']),
                        json.dumps(file_info.get('embeddings', []))
                    ))
                    
                    # Store dependencies
                    cursor.execute(
                        "DELETE FROM dependencies WHERE file_path = ?",
                        (rel_path,)
                    )
                    
                    for dep in file_info['dependencies']:
                        cursor.execute("""
                            INSERT INTO dependencies 
                            (file_path, dependency_path, dependency_type, line_number)
                            VALUES (?, ?, ?, ?)
                        """, (
                            rel_path,
                            dep['path'],
                            dep['type'],
                            dep.get('line', 0)
                        ))
                    
                    # Store symbols
                    for symbol in file_info['symbols']:
                        cursor.execute("""
                            INSERT OR REPLACE INTO symbols 
                            (symbol_name, symbol_type, file_path, line_number, definition)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            symbol['name'],
                            symbol['type'],
                            rel_path,
                            symbol.get('line', 0),
                            symbol.get('definition', '')
                        ))
                    
                    indexed_files += 1
                    
                    # Progress callback
                    if progress_callback:
                        await progress_callback({
                            'current': indexed_files,
                            'total': total_files,
                            'file': rel_path
                        })
                    
                    print(f"📁 Indexed ({indexed_files}/{total_files}): {rel_path}")
                    
                except Exception as e:
                    errors.append({'file': str(file_path), 'error': str(e)})
                    print(f"❌ Error indexing {file_path}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Repository indexing complete! Indexed {indexed_files}/{total_files} files")
        if errors:
            print(f"⚠️ {len(errors)} files had errors during indexing")
        
        return {
            'total_files': total_files,
            'indexed_files': indexed_files,
            'errors': errors
        }
    
    async def extract_file_info(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Extract comprehensive information from a file
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary containing extracted information
        """
        info = {
            'indexed_content': '',
            'dependencies': [],
            'symbols': [],
            'embeddings': []
        }
        
        # Language-specific extraction
        if file_path.suffix == '.py':
            info.update(self.extract_python_info(content))
        elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            info.update(self.extract_javascript_info(content))
        elif file_path.suffix in ['.json']:
            info.update(self.extract_json_info(content))
        elif file_path.suffix in ['.md']:
            info.update(self.extract_markdown_info(content))
        else:
            # Generic text extraction
            info['indexed_content'] = content[:2000]
        
        # Generate embeddings for semantic search
        if info['indexed_content']:
            try:
                # Use existing embedding engine from real_embeddings.py
                embedding = await self.generate_embedding(info['indexed_content'])
                if embedding:
                    info['embeddings'] = embedding
            except Exception as e:
                print(f"Warning: Could not generate embedding: {e}")
        
        return info
    
    def extract_python_info(self, content: str) -> Dict[str, Any]:
        """Extract information from Python files"""
        info = {
            'indexed_content': '',
            'dependencies': [],
            'symbols': []
        }
        
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info['dependencies'].append({
                            'path': alias.name,
                            'type': 'python_import',
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        info['dependencies'].append({
                            'path': f"{module}.{alias.name}",
                            'type': 'python_from_import',
                            'line': node.lineno
                        })
                
                # Extract function and class definitions
                elif isinstance(node, ast.FunctionDef):
                    info['symbols'].append({
                        'name': node.name,
                        'type': 'function',
                        'line': node.lineno,
                        'definition': ast.get_docstring(node) or ''
                    })
                elif isinstance(node, ast.ClassDef):
                    info['symbols'].append({
                        'name': node.name,
                        'type': 'class',
                        'line': node.lineno,
                        'definition': ast.get_docstring(node) or ''
                    })
            
            # Extract searchable content
            lines = content.split('\n')
            searchable_lines = []
            for line in lines:
                stripped = line.strip()
                if (stripped.startswith('#') or 
                    stripped.startswith('"""') or 
                    'def ' in stripped or 
                    'class ' in stripped):
                    searchable_lines.append(stripped)
            
            info['indexed_content'] = '\n'.join(searchable_lines[:100])
            
        except SyntaxError:
            # If parsing fails, fall back to regex
            info['indexed_content'] = self.extract_searchable_content_regex(content)
        
        return info
    
    def extract_javascript_info(self, content: str) -> Dict[str, Any]:
        """Extract information from JavaScript/TypeScript files"""
        info = {
            'indexed_content': '',
            'dependencies': [],
            'symbols': []
        }
        
        # Extract imports
        import_patterns = [
            r'import\s+(?:{[^}]+}|[^\s]+)\s+from\s+["\']([^"\']+)["\']',
            r'require\(["\']([^"\']+)["\']\)',
            r'import\(["\']([^"\']+)["\']\)'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                info['dependencies'].append({
                    'path': match.group(1),
                    'type': 'js_import',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        # Extract function and class definitions
        function_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>',
            r'class\s+(\w+)(?:\s+extends\s+\w+)?'
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                symbol_type = 'class' if 'class' in pattern else 'function'
                info['symbols'].append({
                    'name': match.group(1),
                    'type': symbol_type,
                    'line': content[:match.start()].count('\n') + 1,
                    'definition': ''
                })
        
        # Extract searchable content
        info['indexed_content'] = self.extract_searchable_content_regex(content)
        
        return info
    
    def extract_json_info(self, content: str) -> Dict[str, Any]:
        """Extract information from JSON files"""
        info = {
            'indexed_content': '',
            'dependencies': [],
            'symbols': []
        }
        
        try:
            data = json.loads(content)
            
            # For package.json files
            if isinstance(data, dict):
                if 'dependencies' in data:
                    for dep in data.get('dependencies', {}):
                        info['dependencies'].append({
                            'path': dep,
                            'type': 'npm_dependency'
                        })
                
                if 'devDependencies' in data:
                    for dep in data.get('devDependencies', {}):
                        info['dependencies'].append({
                            'path': dep,
                            'type': 'npm_dev_dependency'
                        })
                
                # Extract main keys as symbols
                for key in data.keys():
                    info['symbols'].append({
                        'name': key,
                        'type': 'json_key',
                        'line': 0,
                        'definition': str(data[key])[:100]
                    })
            
            info['indexed_content'] = json.dumps(data, indent=2)[:1000]
            
        except json.JSONDecodeError:
            info['indexed_content'] = content[:1000]
        
        return info
    
    def extract_markdown_info(self, content: str) -> Dict[str, Any]:
        """Extract information from Markdown files"""
        info = {
            'indexed_content': '',
            'dependencies': [],
            'symbols': []
        }
        
        # Extract headers as symbols
        header_pattern = r'^(#{1,6})\s+(.+)$'
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2)
            info['symbols'].append({
                'name': title,
                'type': f'heading_{level}',
                'line': content[:match.start()].count('\n') + 1,
                'definition': ''
            })
        
        # Extract code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        for match in re.finditer(code_block_pattern, content, re.DOTALL):
            language = match.group(1) or 'code'
            info['symbols'].append({
                'name': f'Code block ({language})',
                'type': 'code_block',
                'line': content[:match.start()].count('\n') + 1,
                'definition': match.group(2)[:200]
            })
        
        info['indexed_content'] = content[:2000]
        
        return info
    
    def extract_searchable_content_regex(self, content: str) -> str:
        """Extract searchable content using regex patterns"""
        lines = content.split('\n')
        searchable_lines = []
        
        for line in lines[:200]:  # Limit to first 200 lines
            stripped = line.strip()
            # Include comments, function definitions, class definitions
            if (stripped.startswith('#') or 
                stripped.startswith('//') or
                re.search(r'\b(def|class|function|const|let|var|export|import)\b', stripped)):
                searchable_lines.append(stripped)
        
        return '\n'.join(searchable_lines[:100])
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during indexing"""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.next', 'dist', 'build',
            '.DS_Store', '.env', '*.log', '*.tmp', '*.cache', '.pyc',
            'venv', '.venv', 'env', '.idea', '.vscode', '*.egg-info'
        ]
        
        path_str = str(file_path)
        
        # Check patterns
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        
        # Check file size (ignore files > 10MB)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return True
        except:
            pass
        
        return False
    
    async def search_codebase(self, query: str, file_types: Optional[List[str]] = None,
                            limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search through the indexed codebase
        
        Args:
            query: Search query
            file_types: Optional list of file extensions to filter
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build SQL query
        sql = """
            SELECT path, file_type, indexed_content, symbols 
            FROM file_index 
            WHERE indexed_content LIKE ?
        """
        params = [f"%{query}%"]
        
        if file_types:
            placeholders = ",".join("?" * len(file_types))
            sql += f" AND file_type IN ({placeholders})"
            params.extend(file_types)
        
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql, params)
        results = []
        
        for row in cursor.fetchall():
            path, file_type, content, symbols_json = row
            
            # Find matching lines
            matching_lines = []
            for i, line in enumerate(content.split('\n')):
                if query.lower() in line.lower():
                    matching_lines.append({
                        'line_number': i + 1,
                        'content': line.strip()[:200]
                    })
            
            results.append({
                'path': path,
                'file_type': file_type,
                'matching_lines': matching_lines[:5],
                'symbols': json.loads(symbols_json) if symbols_json else []
            })
        
        conn.close()
        return results
    
    async def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get dependencies for a specific file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get direct dependencies
        cursor.execute("""
            SELECT dependency_path, dependency_type, line_number 
            FROM dependencies 
            WHERE file_path = ?
            ORDER BY line_number
        """, (file_path,))
        
        dependencies = []
        for row in cursor.fetchall():
            dependencies.append({
                'path': row[0],
                'type': row[1],
                'line': row[2]
            })
        
        # Get files that depend on this file
        cursor.execute("""
            SELECT file_path 
            FROM dependencies 
            WHERE dependency_path LIKE ?
        """, (f"%{file_path}%",))
        
        dependents = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'file': file_path,
            'dependencies': dependencies,
            'dependents': dependents
        }
    
    async def get_symbol_definition(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find symbol definitions across the codebase"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol_name, symbol_type, file_path, line_number, definition 
            FROM symbols 
            WHERE symbol_name = ? OR symbol_name LIKE ?
            LIMIT 10
        """, (symbol_name, f"%{symbol_name}%"))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'name': row[0],
                'type': row[1],
                'file': row[2],
                'line': row[3],
                'definition': row[4]
            })
        
        conn.close()
        return results
    
    async def update_dashboard_context(self, component: str, state: Dict[str, Any]):
        """Update dashboard context state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_context 
            (component, state, last_updated)
            VALUES (?, ?, ?)
        """, (component, json.dumps(state), datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f"🎛️ Updated dashboard context for: {component}")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using the existing embedding engine"""
        try:
            # This would integrate with the real_embeddings.py module
            # For now, return None as placeholder
            return None
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None


# CLI interface for testing
async def main():
    """Main function for testing the repository indexer"""
    import sys
    
    repo_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"🚀 Initializing Repository Indexer for: {repo_path}")
    
    indexer = RepositoryIndexer(repo_path)
    
    # Perform indexing
    results = await indexer.index_repository()
    
    print(f"\n📊 Indexing Results:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Indexed files: {results['indexed_files']}")
    print(f"  Errors: {len(results['errors'])}")
    
    # Test search
    if len(sys.argv) > 2:
        query = sys.argv[2]
        print(f"\n🔍 Searching for: {query}")
        search_results = await indexer.search_codebase(query)
        
        for result in search_results[:5]:
            print(f"\n📄 {result['path']}")
            for line in result['matching_lines']:
                print(f"  Line {line['line_number']}: {line['content']}")


if __name__ == "__main__":
    asyncio.run(main())