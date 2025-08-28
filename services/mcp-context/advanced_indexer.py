"""
Advanced Code Context Indexer for MCP
Provides intelligent codebase understanding with:
- Incremental indexing on file changes
- Semantic code understanding
- Dependency tracking
- Symbol relationships
- Auto-evolution on commits
"""

import os
import ast
import git
import hashlib
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import redis
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import json

app = FastAPI(title="MCP Advanced Context Indexer")

# Redis for caching and change tracking
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class CodebaseIndex:
    """Main codebase indexing system"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path) if os.path.exists(f"{repo_path}/.git") else None
        self.index = {}
        self.symbol_graph = {}
        self.file_hashes = {}
        self.dependencies = {}
        
    async def full_index(self):
        """Perform full codebase indexing"""
        print(f"Starting full index of {self.repo_path}")
        
        for file_path in self.repo_path.rglob("*.py"):
            await self.index_file(file_path)
            
        # Build symbol relationships
        await self.build_symbol_graph()
        
        # Cache in Redis
        await self.cache_index()
        
        return {
            "files_indexed": len(self.index),
            "symbols_found": sum(len(f["symbols"]) for f in self.index.values()),
            "relationships": len(self.symbol_graph)
        }
    
    async def index_file(self, file_path: Path):
        """Index a single Python file"""
        relative_path = file_path.relative_to(self.repo_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Calculate file hash for change detection
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Skip if unchanged
            if self.file_hashes.get(str(relative_path)) == file_hash:
                return
                
            self.file_hashes[str(relative_path)] = file_hash
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract symbols
            symbols = self.extract_symbols(tree, str(relative_path))
            
            # Extract imports and dependencies
            imports = self.extract_imports(tree)
            
            # Store in index
            self.index[str(relative_path)] = {
                "path": str(relative_path),
                "hash": file_hash,
                "symbols": symbols,
                "imports": imports,
                "last_indexed": datetime.now().isoformat(),
                "lines": len(content.splitlines()),
                "size": len(content)
            }
            
            # Track dependencies
            self.dependencies[str(relative_path)] = imports
            
        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
    
    def extract_symbols(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Extract all symbols from AST"""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "line": node.lineno,
                    "file": file_path,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    "bases": [self.get_name(base) for base in node.bases]
                })
            elif isinstance(node, ast.FunctionDef):
                symbols.append({
                    "name": node.name,
                    "type": "function",
                    "line": node.lineno,
                    "file": file_path,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [self.get_name(d) for d in node.decorator_list]
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append({
                    "name": node.name,
                    "type": "async_function",
                    "line": node.lineno,
                    "file": file_path,
                    "args": [arg.arg for arg in node.args.args]
                })
                
        return symbols
    
    def extract_imports(self, tree: ast.AST) -> List[Dict]:
        """Extract all imports from AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "type": "import"
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "type": "from_import"
                    })
                    
        return imports
    
    def get_name(self, node):
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    async def build_symbol_graph(self):
        """Build relationships between symbols"""
        self.symbol_graph = {}
        
        # Map all symbols to their locations
        symbol_map = {}
        for file_path, file_data in self.index.items():
            for symbol in file_data["symbols"]:
                symbol_key = f"{symbol['name']}:{symbol['type']}"
                if symbol_key not in symbol_map:
                    symbol_map[symbol_key] = []
                symbol_map[symbol_key].append({
                    "file": file_path,
                    "line": symbol["line"],
                    **symbol
                })
        
        # Build relationships
        for file_path, file_data in self.index.items():
            # Check imports for relationships
            for imp in file_data["imports"]:
                if imp["name"] in symbol_map:
                    if file_path not in self.symbol_graph:
                        self.symbol_graph[file_path] = {"imports": [], "imported_by": []}
                    self.symbol_graph[file_path]["imports"].append(imp["name"])
        
        return self.symbol_graph
    
    async def cache_index(self):
        """Cache index in Redis"""
        # Store main index
        redis_client.set(
            f"codebase_index:{self.repo_path}",
            json.dumps(self.index),
            ex=3600  # 1 hour expiry
        )
        
        # Store symbol graph
        redis_client.set(
            f"symbol_graph:{self.repo_path}",
            json.dumps(self.symbol_graph),
            ex=3600
        )
        
        # Store file hashes for change detection
        redis_client.hset(
            f"file_hashes:{self.repo_path}",
            mapping=self.file_hashes
        )
    
    async def incremental_update(self, changed_files: List[str]):
        """Update index for changed files only"""
        updated = []
        
        for file_path in changed_files:
            full_path = self.repo_path / file_path
            if full_path.exists() and full_path.suffix == '.py':
                await self.index_file(full_path)
                updated.append(file_path)
        
        # Rebuild affected parts of symbol graph
        if updated:
            await self.build_symbol_graph()
            await self.cache_index()
        
        return {"updated_files": updated}
    
    async def get_context_for_symbol(self, symbol_name: str) -> Dict:
        """Get comprehensive context for a symbol"""
        context = {
            "symbol": symbol_name,
            "definitions": [],
            "usages": [],
            "related_symbols": [],
            "dependencies": []
        }
        
        # Find definitions
        for file_path, file_data in self.index.items():
            for symbol in file_data["symbols"]:
                if symbol["name"] == symbol_name:
                    context["definitions"].append({
                        "file": file_path,
                        "line": symbol["line"],
                        "type": symbol["type"],
                        "details": symbol
                    })
        
        # Find usages (simplified - would need more sophisticated analysis)
        for file_path, file_data in self.index.items():
            for imp in file_data["imports"]:
                if imp.get("name") == symbol_name:
                    context["usages"].append({
                        "file": file_path,
                        "import_type": imp["type"]
                    })
        
        # Find related symbols
        for definition in context["definitions"]:
            file_data = self.index.get(definition["file"])
            if file_data:
                for symbol in file_data["symbols"]:
                    if symbol["name"] != symbol_name:
                        context["related_symbols"].append({
                            "name": symbol["name"],
                            "type": symbol["type"],
                            "file": definition["file"]
                        })
        
        return context

class FileChangeHandler(FileSystemEventHandler):
    """Watch for file changes and trigger incremental indexing"""
    
    def __init__(self, indexer: CodebaseIndex):
        self.indexer = indexer
        self.pending_updates = set()
        self.last_update = datetime.now()
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            self.pending_updates.add(event.src_path)
            # Debounce - wait 2 seconds before processing
            asyncio.create_task(self.process_updates())
    
    async def process_updates(self):
        await asyncio.sleep(2)
        if self.pending_updates:
            files = list(self.pending_updates)
            self.pending_updates.clear()
            await self.indexer.incremental_update(files)

# API Endpoints
indexer = None
observer = None

@app.on_event("startup")
async def startup():
    global indexer, observer
    # Initialize with current directory or configured path
    repo_path = os.getenv("REPO_PATH", "/Users/lynnmusil/sophia-ai-intel-1")
    indexer = CodebaseIndex(repo_path)
    
    # Start file watcher
    event_handler = FileChangeHandler(indexer)
    observer = Observer()
    observer.schedule(event_handler, repo_path, recursive=True)
    observer.start()
    
    # Perform initial indexing
    await indexer.full_index()

@app.on_event("shutdown")
async def shutdown():
    if observer:
        observer.stop()
        observer.join()

@app.get("/")
async def root():
    return {
        "service": "MCP Advanced Context Indexer",
        "capabilities": [
            "incremental_indexing",
            "symbol_extraction",
            "dependency_tracking",
            "change_detection",
            "semantic_search",
            "auto_evolution"
        ]
    }

@app.get("/index/status")
async def get_index_status():
    """Get current index status"""
    if not indexer:
        return {"status": "not_initialized"}
    
    return {
        "status": "active",
        "files_indexed": len(indexer.index),
        "total_symbols": sum(len(f["symbols"]) for f in indexer.index.values()),
        "last_update": max(
            (f["last_indexed"] for f in indexer.index.values()),
            default="never"
        )
    }

@app.post("/index/refresh")
async def refresh_index(background_tasks: BackgroundTasks):
    """Trigger full re-indexing"""
    background_tasks.add_task(indexer.full_index)
    return {"status": "indexing_started"}

@app.get("/context/{symbol_name}")
async def get_symbol_context(symbol_name: str):
    """Get context for a specific symbol"""
    if not indexer:
        return {"error": "indexer not initialized"}
    
    context = await indexer.get_context_for_symbol(symbol_name)
    return context

@app.post("/index/git-hook")
async def handle_git_hook(commit_data: Dict):
    """Handle git commit hooks for auto-evolution"""
    # Extract changed files from commit
    changed_files = commit_data.get("changed_files", [])
    
    if changed_files:
        result = await indexer.incremental_update(changed_files)
        return {"status": "updated", **result}
    
    return {"status": "no_changes"}

class QueryRequest(BaseModel):
    query: str
    context_depth: int = 2
    include_dependencies: bool = True

@app.post("/query")
async def query_codebase(request: QueryRequest):
    """Intelligent codebase querying"""
    # This would integrate with LLM for natural language queries
    # For now, return relevant symbols
    results = []
    
    for file_path, file_data in indexer.index.items():
        for symbol in file_data["symbols"]:
            if request.query.lower() in symbol["name"].lower():
                results.append({
                    "symbol": symbol["name"],
                    "type": symbol["type"],
                    "file": file_path,
                    "line": symbol["line"],
                    "context": await indexer.get_context_for_symbol(symbol["name"])
                    if request.context_depth > 0 else None
                })
    
    return {
        "query": request.query,
        "results": results[:10],  # Limit results
        "total_matches": len(results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
