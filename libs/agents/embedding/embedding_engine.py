"""
Sophia AI Embedding Engine

Advanced code embedding system for semantic understanding and retrieval.
Supports multiple embedding models and chunking strategies optimized for code.

Key Features:
- Multi-language code chunking (Python, TypeScript, JavaScript, SQL)
- Hierarchical embeddings (file → function → line level)
- Semantic similarity search
- Integration with vector databases
- Incremental updates and versioning

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import ast
import tiktoken
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Types of code chunks"""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    BLOCK = "block"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    IMPORT = "import"
    VARIABLE = "variable"


class EmbeddingModel(Enum):
    """Supported embedding models"""
    CODE_BERT = "microsoft/codebert-base"
    UNIXCODER = "microsoft/unixcoder-base"
    CODE_T5 = "Salesforce/codet5-base"
    SENTENCE_TRANSFORMERS = "all-mpnet-base-v2"
    OPENAI_ADA = "text-embedding-ada-002"


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    id: str
    content: str
    chunk_type: ChunkType
    language: str
    file_path: str
    start_line: int
    end_line: int
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}
        if self.hash is None:
            self.hash = self._calculate_hash()
        if self.created_at is None:
            self.created_at = datetime.now()

    def _calculate_hash(self) -> str:
        """Calculate content hash for change detection"""
        content_str = f"{self.content}{self.file_path}{self.start_line}{self.end_line}"
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            **asdict(self),
            'chunk_type': self.chunk_type.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        """Create from dictionary"""
        data['chunk_type'] = ChunkType(data['chunk_type'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class SearchResult:
    """Search result with similarity score"""
    chunk: CodeChunk
    similarity_score: float
    context_chunks: List[CodeChunk] = None
    explanation: Optional[str] = None

    def __post_init__(self):
        if self.context_chunks is None:
            self.context_chunks = []


class CodeChunker:
    """
    Intelligent code chunking system that understands code structure
    """
    
    def __init__(self):
        self.language_processors = {
            'python': self._chunk_python,
            'typescript': self._chunk_typescript,
            'javascript': self._chunk_javascript,
            'sql': self._chunk_sql,
            'json': self._chunk_json,
            'markdown': self._chunk_markdown
        }
        
        # Tokenizer for length estimation
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not load tiktoken: {e}. Using character count fallback.")
            self.tokenizer = None

    async def chunk_file(self, file_path: str, content: str, language: str) -> List[CodeChunk]:
        """Chunk a file into semantic code chunks"""
        if language in self.language_processors:
            return await self.language_processors[language](file_path, content)
        else:
            return await self._chunk_generic(file_path, content, language)

    async def _chunk_python(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk Python code using AST"""
        chunks = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # File-level chunk
            file_chunk = CodeChunk(
                id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
                content=content,
                chunk_type=ChunkType.FILE,
                language='python',
                file_path=file_path,
                start_line=1,
                end_line=len(lines),
                metadata={
                    'total_lines': len(lines),
                    'has_classes': any(isinstance(node, ast.ClassDef) for node in ast.walk(tree)),
                    'has_functions': any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree)),
                    'imports': self._extract_python_imports(tree)
                }
            )
            chunks.append(file_chunk)
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_chunk = await self._create_python_class_chunk(node, lines, file_path, file_chunk.id)
                    chunks.append(class_chunk)
                    file_chunk.children_ids.append(class_chunk.id)
                    
                    # Extract methods within class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_chunk = await self._create_python_method_chunk(
                                item, lines, file_path, class_chunk.id, node.name
                            )
                            chunks.append(method_chunk)
                            class_chunk.children_ids.append(method_chunk.id)
                
                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                    if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
                ):
                    # Top-level function
                    func_chunk = await self._create_python_function_chunk(node, lines, file_path, file_chunk.id)
                    chunks.append(func_chunk)
                    file_chunk.children_ids.append(func_chunk.id)
            
            # Extract docstrings and comments
            docstring_chunks = await self._extract_python_docstrings_and_comments(content, lines, file_path)
            chunks.extend(docstring_chunks)
            
            return chunks
            
        except SyntaxError as e:
            logger.warning(f"Python syntax error in {file_path}: {e}")
            return await self._chunk_generic(file_path, content, 'python')

    async def _create_python_class_chunk(
        self, node: ast.ClassDef, lines: List[str], file_path: str, parent_id: str
    ) -> CodeChunk:
        """Create chunk for Python class"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        class_content = '\n'.join(lines[start_line-1:end_line])
        
        return CodeChunk(
            id=f"class_{node.name}_{hashlib.md5(f'{file_path}_{node.name}'.encode()).hexdigest()[:8]}",
            content=class_content,
            chunk_type=ChunkType.CLASS,
            language='python',
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_id=parent_id,
            metadata={
                'class_name': node.name,
                'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)],
                'decorators': [dec.id for dec in node.decorator_list if isinstance(dec, ast.Name)],
                'methods': [item.name for item in node.body if isinstance(item, ast.FunctionDef)],
                'docstring': ast.get_docstring(node)
            }
        )

    async def _create_python_function_chunk(
        self, node: ast.FunctionDef, lines: List[str], file_path: str, parent_id: str
    ) -> CodeChunk:
        """Create chunk for Python function"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        func_content = '\n'.join(lines[start_line-1:end_line])
        
        return CodeChunk(
            id=f"func_{node.name}_{hashlib.md5(f'{file_path}_{node.name}'.encode()).hexdigest()[:8]}",
            content=func_content,
            chunk_type=ChunkType.FUNCTION,
            language='python',
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_id=parent_id,
            metadata={
                'function_name': node.name,
                'args': [arg.arg for arg in node.args.args],
                'decorators': [dec.id for dec in node.decorator_list if isinstance(dec, ast.Name)],
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'docstring': ast.get_docstring(node),
                'returns': self._get_python_return_annotation(node)
            }
        )

    async def _create_python_method_chunk(
        self, node: ast.FunctionDef, lines: List[str], file_path: str, parent_id: str, class_name: str
    ) -> CodeChunk:
        """Create chunk for Python method"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        method_content = '\n'.join(lines[start_line-1:end_line])
        
        return CodeChunk(
            id=f"method_{class_name}_{node.name}_{hashlib.md5(f'{file_path}_{class_name}_{node.name}'.encode()).hexdigest()[:8]}",
            content=method_content,
            chunk_type=ChunkType.METHOD,
            language='python',
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_id=parent_id,
            metadata={
                'method_name': node.name,
                'class_name': class_name,
                'args': [arg.arg for arg in node.args.args],
                'decorators': [dec.id for dec in node.decorator_list if isinstance(dec, ast.Name)],
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'is_static': any(dec.id == 'staticmethod' for dec in node.decorator_list if isinstance(dec, ast.Name)),
                'is_class_method': any(dec.id == 'classmethod' for dec in node.decorator_list if isinstance(dec, ast.Name)),
                'docstring': ast.get_docstring(node)
            }
        )

    async def _chunk_typescript(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk TypeScript/JavaScript code using regex patterns"""
        chunks = []
        lines = content.split('\n')
        
        # File-level chunk
        file_chunk = CodeChunk(
            id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
            content=content,
            chunk_type=ChunkType.FILE,
            language='typescript',
            file_path=file_path,
            start_line=1,
            end_line=len(lines),
            metadata={
                'total_lines': len(lines),
                'imports': self._extract_typescript_imports(content),
                'exports': self._extract_typescript_exports(content)
            }
        )
        chunks.append(file_chunk)
        
        # Extract classes
        class_pattern = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_chunk = await self._create_typescript_class_chunk(match, content, lines, file_path, file_chunk.id)
            if class_chunk:
                chunks.append(class_chunk)
                file_chunk.children_ids.append(class_chunk.id)
        
        # Extract functions
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*[^=]+)?\s*=>\s*\{',
            r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*(?::\s*[^=]+)?\s*=>\s*\{'
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_chunk = await self._create_typescript_function_chunk(match, content, lines, file_path, file_chunk.id)
                if func_chunk:
                    chunks.append(func_chunk)
                    file_chunk.children_ids.append(func_chunk.id)
        
        return chunks

    async def _chunk_javascript(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk JavaScript code (similar to TypeScript but without types)"""
        return await self._chunk_typescript(file_path, content)  # Reuse TS logic

    async def _chunk_sql(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk SQL files"""
        chunks = []
        lines = content.split('\n')
        
        # File-level chunk
        file_chunk = CodeChunk(
            id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
            content=content,
            chunk_type=ChunkType.FILE,
            language='sql',
            file_path=file_path,
            start_line=1,
            end_line=len(lines)
        )
        chunks.append(file_chunk)
        
        # Extract major SQL statements
        sql_patterns = [
            (r'CREATE\s+TABLE\s+(\w+)', 'table_creation'),
            (r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)', 'index_creation'),
            (r'CREATE\s+VIEW\s+(\w+)', 'view_creation'),
            (r'CREATE\s+FUNCTION\s+(\w+)', 'function_creation'),
            (r'INSERT\s+INTO\s+(\w+)', 'insert_statement'),
            (r'UPDATE\s+(\w+)', 'update_statement'),
            (r'DELETE\s+FROM\s+(\w+)', 'delete_statement')
        ]
        
        for pattern, stmt_type in sql_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Find the complete statement (until semicolon)
                start_pos = match.start()
                stmt_start_line = content[:start_pos].count('\n') + 1
                
                # Find end of statement
                stmt_end = content.find(';', start_pos)
                if stmt_end == -1:
                    continue
                
                stmt_end_line = content[:stmt_end].count('\n') + 1
                stmt_content = content[start_pos:stmt_end + 1]
                
                stmt_chunk = CodeChunk(
                    id=f"sql_{stmt_type}_{match.group(1)}_{hashlib.md5(f'{file_path}_{stmt_content}'.encode()).hexdigest()[:8]}",
                    content=stmt_content.strip(),
                    chunk_type=ChunkType.FUNCTION,  # Using FUNCTION for SQL statements
                    language='sql',
                    file_path=file_path,
                    start_line=stmt_start_line,
                    end_line=stmt_end_line,
                    parent_id=file_chunk.id,
                    metadata={
                        'statement_type': stmt_type,
                        'object_name': match.group(1)
                    }
                )
                
                chunks.append(stmt_chunk)
                file_chunk.children_ids.append(stmt_chunk.id)
        
        return chunks

    async def _chunk_json(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk JSON files"""
        try:
            data = json.loads(content)
            lines = content.split('\n')
            
            file_chunk = CodeChunk(
                id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
                content=content,
                chunk_type=ChunkType.FILE,
                language='json',
                file_path=file_path,
                start_line=1,
                end_line=len(lines),
                metadata={
                    'json_type': type(data).__name__,
                    'top_level_keys': list(data.keys()) if isinstance(data, dict) else None,
                    'array_length': len(data) if isinstance(data, list) else None
                }
            )
            
            return [file_chunk]
        
        except json.JSONDecodeError:
            return await self._chunk_generic(file_path, content, 'json')

    async def _chunk_markdown(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk Markdown files by sections"""
        chunks = []
        lines = content.split('\n')
        
        # File-level chunk
        file_chunk = CodeChunk(
            id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
            content=content,
            chunk_type=ChunkType.FILE,
            language='markdown',
            file_path=file_path,
            start_line=1,
            end_line=len(lines)
        )
        chunks.append(file_chunk)
        
        # Extract sections by headers
        current_section = None
        section_start = 1
        
        for i, line in enumerate(lines, 1):
            if re.match(r'^#{1,6}\s+', line):
                # End previous section
                if current_section:
                    section_content = '\n'.join(lines[section_start-1:i-1])
                    if section_content.strip():
                        section_chunk = CodeChunk(
                            id=f"section_{current_section}_{hashlib.md5(f'{file_path}_{current_section}'.encode()).hexdigest()[:8]}",
                            content=section_content,
                            chunk_type=ChunkType.BLOCK,
                            language='markdown',
                            file_path=file_path,
                            start_line=section_start,
                            end_line=i-1,
                            parent_id=file_chunk.id,
                            metadata={'section_title': current_section}
                        )
                        chunks.append(section_chunk)
                        file_chunk.children_ids.append(section_chunk.id)
                
                # Start new section
                current_section = re.sub(r'^#{1,6}\s+', '', line).strip()
                section_start = i
        
        # Handle last section
        if current_section:
            section_content = '\n'.join(lines[section_start-1:])
            if section_content.strip():
                section_chunk = CodeChunk(
                    id=f"section_{current_section}_{hashlib.md5(f'{file_path}_{current_section}'.encode()).hexdigest()[:8]}",
                    content=section_content,
                    chunk_type=ChunkType.BLOCK,
                    language='markdown',
                    file_path=file_path,
                    start_line=section_start,
                    end_line=len(lines),
                    parent_id=file_chunk.id,
                    metadata={'section_title': current_section}
                )
                chunks.append(section_chunk)
                file_chunk.children_ids.append(section_chunk.id)
        
        return chunks

    async def _chunk_generic(self, file_path: str, content: str, language: str) -> List[CodeChunk]:
        """Generic chunking for unsupported languages"""
        lines = content.split('\n')
        max_chunk_size = 500  # lines
        
        chunks = []
        
        # File-level chunk
        file_chunk = CodeChunk(
            id=f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
            content=content,
            chunk_type=ChunkType.FILE,
            language=language,
            file_path=file_path,
            start_line=1,
            end_line=len(lines)
        )
        chunks.append(file_chunk)
        
        # Split into smaller chunks if too large
        if len(lines) > max_chunk_size:
            for i in range(0, len(lines), max_chunk_size):
                chunk_lines = lines[i:i + max_chunk_size]
                chunk_content = '\n'.join(chunk_lines)
                
                chunk = CodeChunk(
                    id=f"block_{i}_{hashlib.md5(f'{file_path}_{i}'.encode()).hexdigest()[:8]}",
                    content=chunk_content,
                    chunk_type=ChunkType.BLOCK,
                    language=language,
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=min(i + max_chunk_size, len(lines)),
                    parent_id=file_chunk.id
                )
                
                chunks.append(chunk)
                file_chunk.children_ids.append(chunk.id)
        
        return chunks

    # Helper methods for extracting metadata
    def _extract_python_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from Python AST"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _extract_typescript_imports(self, content: str) -> List[str]:
        """Extract import statements from TypeScript/JavaScript"""
        import_pattern = r'import.*?from\s+[\'"]([^\'"]+)[\'"]'
        return re.findall(import_pattern, content)

    def _extract_typescript_exports(self, content: str) -> List[str]:
        """Extract export statements from TypeScript/JavaScript"""
        export_pattern = r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
        return re.findall(export_pattern, content)

    def _get_python_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation from Python function"""
        if node.returns:
            return ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        return None

    async def _extract_python_docstrings_and_comments(
        self, content: str, lines: List[str], file_path: str
    ) -> List[CodeChunk]:
        """Extract docstrings and comments as separate chunks"""
        chunks = []
        
        # Extract comments
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') and len(stripped) > 1:
                comment_chunk = CodeChunk(
                    id=f"comment_{i}_{hashlib.md5(f'{file_path}_{line}'.encode()).hexdigest()[:8]}",
                    content=stripped,
                    chunk_type=ChunkType.COMMENT,
                    language='python',
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    metadata={'comment_text': stripped[1:].strip()}
                )
                chunks.append(comment_chunk)
        
        return chunks

    async def _create_typescript_class_chunk(
        self, match: re.Match, content: str, lines: List[str], file_path: str, parent_id: str
    ) -> Optional[CodeChunk]:
        """Create TypeScript class chunk"""
        class_name = match.group(1)
        start_pos = match.start()
        start_line = content[:start_pos].count('\n') + 1
        
        # Find matching brace
        brace_count = 0
        in_class = False
        end_pos = start_pos
        
        for i in range(start_pos, len(content)):
            char = content[i]
            if char == '{':
                brace_count += 1
                in_class = True
            elif char == '}':
                brace_count -= 1
                if in_class and brace_count == 0:
                    end_pos = i + 1
                    break
        
        if not in_class:
            return None
        
        end_line = content[:end_pos].count('\n') + 1
        class_content = content[start_pos:end_pos]
        
        return CodeChunk(
            id=f"class_{class_name}_{hashlib.md5(f'{file_path}_{class_name}'.encode()).hexdigest()[:8]}",
            content=class_content,
            chunk_type=ChunkType.CLASS,
            language='typescript',
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_id=parent_id,
            metadata={'class_name': class_name}
        )

    async def _create_typescript_function_chunk(
        self, match: re.Match, content: str, lines: List[str], file_path: str, parent_id: str
    ) -> Optional[CodeChunk]:
        """Create TypeScript function chunk"""
        func_name = match.group(1)
        start_pos = match.start()
        start_line = content[:start_pos].count('\n') + 1
        
        # Find function end (simplified - would need better parsing for complex cases)
        brace_count = 0
        in_function = False
        end_pos = start_pos
        
        for i in range(start_pos, len(content)):
            char = content[i]
            if char == '{':
                brace_count += 1
                in_function = True
            elif char == '}':
                brace_count -= 1
                if in_function and brace_count == 0:
                    end_pos = i + 1
                    break
        
        if not in_function:
            return None
        
        end_line = content[:end_pos].count('\n') + 1
        func_content = content[start_pos:end_pos]
        
        return CodeChunk(
            id=f"func_{func_name}_{hashlib.md5(f'{file_path}_{func_name}'.encode()).hexdigest()[:8]}",
            content=func_content,
            chunk_type=ChunkType.FUNCTION,
            language='typescript',
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_id=parent_id,
            metadata={'function_name': func_name}
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimate: ~4 characters per token
            return len(text) // 4


class EmbeddingEngine:
    """
    Main embedding engine that combines chunking and embedding generation
    """
    
    def __init__(
        self,
        embedding_model: str = "all-mpnet-base-v2",
        chunk_overlap: int = 50,
        max_chunk_tokens: int = 512
    ):
        self.chunker = CodeChunker()
        self.embedding_model_name = embedding_model
        self.chunk_overlap = chunk_overlap
        self.max_chunk_tokens = max_chunk_tokens
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {embedding_model}: {e}")
            # Fallback to a basic model
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Cache for embeddings
        self.embedding_cache: Dict[str, List[float]] = {}

    async def process_file(
        self,
        file_path: str,
        content: str,
        language: str,
        force_refresh: bool = False
    ) -> List[CodeChunk]:
        """Process a file into embedded chunks"""
        logger.info(f"Processing file: {file_path} ({language})")
        
        # Chunk the file
        chunks = await self.chunker.chunk_file(file_path, content, language)
        
        # Generate embeddings for each chunk
        embedded_chunks = []
        for chunk in chunks:
            # Check cache if not forcing refresh
            if not force_refresh and chunk.hash in self.embedding_cache:
                chunk.embedding = self.embedding_cache[chunk.hash]
                chunk.embedding_model = self.embedding_model_name
                embedded_chunks.append(chunk)
                continue
            
            # Generate new embedding
            try:
                embedding = await self._generate_embedding(chunk.content)
                chunk.embedding = embedding
                chunk.embedding_model = self.embedding_model_name
                chunk.updated_at = datetime.now()
                
                # Cache the embedding
                self.embedding_cache[chunk.hash] = embedding
                
                embedded_chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {chunk.id}: {e}")
                # Add chunk without embedding for now
                embedded_chunks.append(chunk)
        
        logger.info(f"Processed {len(embedded_chunks)} chunks for {file_path}")
        return embedded_chunks

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # Preprocess text for better embeddings
        processed_text = self._preprocess_text_for_embedding(text)
        
        # Generate embedding
        embedding = self.embedding_model.encode(processed_text, convert_to_numpy=True)
        return embedding.tolist()

    def _preprocess_text_for_embedding(self, text: str) -> str:
        """Preprocess text for better embedding quality"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Limit length for embedding model
        if self.chunker.estimate_tokens(text) > self.max_chunk_tokens:
            # Truncate while trying to preserve meaningful content
            lines = text.split('\n')
            truncated_lines = []
            token_count = 0
            
            for line in lines:
                line_tokens = self.chunker.estimate_tokens(line)
                if token_count + line_tokens > self.max_chunk_tokens:
                    break
                truncated_lines.append(line)
                token_count += line_tokens
            
            text = '\n'.join(truncated_lines)
        
        return text.strip()

    async def search_similar(
        self,
        query: str,
        chunks: List[CodeChunk],
        top_k: int = 10,
        similarity_threshold: float = 0.5,
        filter_by_type: Optional[List[ChunkType]] = None,
        filter_by_language: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for similar code chunks"""
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        query_vector = np.array(query_embedding)
        
        # Calculate similarities
        results = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
                
            # Apply filters
            if filter_by_type and chunk.chunk_type not in filter_by_type:
                continue
            if filter_by_language and chunk.language not in filter_by_language:
                continue
            
            # Calculate cosine similarity
            chunk_vector = np.array(chunk.embedding)
            similarity = np.dot(query_vector, chunk_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
            )
            
            if similarity >= similarity_threshold:
                # Find context chunks (parent and children)
                context_chunks = await self._get_context_chunks(chunk, chunks)
                
                result = SearchResult(
                    chunk=chunk,
                    similarity_score=float(similarity),
                    context_chunks=context_chunks,
                    explanation=self._generate_similarity_explanation(query, chunk, similarity)
                )
                results.append(result)
        
        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]

    async def _get_context_chunks(self, target_chunk: CodeChunk, all_chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Get context chunks (parent and children) for a target chunk"""
        context = []
        
        # Find parent
        if target_chunk.parent_id:
            parent = next((c for c in all_chunks if c.id == target_chunk.parent_id), None)
            if parent:
                context.append(parent)
        
        # Find children
        for child_id in target_chunk.children_ids:
            child = next((c for c in all_chunks if c.id == child_id), None)
            if child:
                context.append(child)
        
        return context

    def _generate_similarity_explanation(self, query: str, chunk: CodeChunk, similarity: float) -> str:
        """Generate explanation for why this chunk is similar"""
        explanation_parts = [
            f"Similarity score: {similarity:.3f}",
            f"Chunk type: {chunk.chunk_type.value}",
            f"Language: {chunk.language}",
            f"File: {chunk.file_path}"
        ]
        
        # Add specific explanations based on chunk type
        if chunk.chunk_type == ChunkType.FUNCTION and 'function_name' in chunk.metadata:
            explanation_parts.append(f"Function: {chunk.metadata['function_name']}")
        elif chunk.chunk_type == ChunkType.CLASS and 'class_name' in chunk.metadata:
            explanation_parts.append(f"Class: {chunk.metadata['class_name']}")
        elif chunk.chunk_type == ChunkType.METHOD and 'method_name' in chunk.metadata:
            explanation_parts.append(f"Method: {chunk.metadata['class_name']}.{chunk.metadata['method_name']}")
        
        return " | ".join(explanation_parts)

    async def update_chunk_embedding(self, chunk: CodeChunk, force: bool = False) -> CodeChunk:
        """Update embedding for a single chunk"""
        if chunk.embedding and not force:
            return chunk
        
        try:
            embedding = await self._generate_embedding(chunk.content)
            chunk.embedding = embedding
            chunk.embedding_model = self.embedding_model_name
            chunk.updated_at = datetime.now()
            
            # Update cache
            self.embedding_cache[chunk.hash] = embedding
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to update embedding for chunk {chunk.id}: {e}")
            return chunk

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings"""
        return {
            "model_name": self.embedding_model_name,
            "cache_size": len(self.embedding_cache),
            "max_chunk_tokens": self.max_chunk_tokens,
            "chunk_overlap": self.chunk_overlap
        }

    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")

    async def batch_process_chunks(
        self,
        chunks: List[CodeChunk],
        batch_size: int = 32
    ) -> List[CodeChunk]:
        """Process multiple chunks in batches for efficiency"""
        embedded_chunks = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = []
            batch_chunks = []
            
            # Prepare batch
            for chunk in batch:
                if chunk.embedding is None:
                    processed_text = self._preprocess_text_for_embedding(chunk.content)
                    batch_texts.append(processed_text)
                    batch_chunks.append(chunk)
                else:
                    embedded_chunks.append(chunk)
            
            # Generate embeddings for batch
            if batch_texts:
                try:
                    batch_embeddings = self.embedding_model.encode(
                        batch_texts, 
                        convert_to_numpy=True,
                        batch_size=batch_size
                    )
                    
                    # Assign embeddings to chunks
                    for chunk, embedding in zip(batch_chunks, batch_embeddings):
                        chunk.embedding = embedding.tolist()
                        chunk.embedding_model = self.embedding_model_name
                        chunk.updated_at = datetime.now()
                        
                        # Cache the embedding
                        self.embedding_cache[chunk.hash] = chunk.embedding
                        
                        embedded_chunks.append(chunk)
                        
                except Exception as e:
                    logger.error(f"Failed to process batch: {e}")
                    # Add chunks without embeddings
                    embedded_chunks.extend(batch_chunks)
        
        return embedded_chunks

    def calculate_similarity(self, chunk1: CodeChunk, chunk2: CodeChunk) -> float:
        """Calculate similarity between two chunks"""
        if not chunk1.embedding or not chunk2.embedding:
            return 0.0
        
        vec1 = np.array(chunk1.embedding)
        vec2 = np.array(chunk2.embedding)
        
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    async def find_duplicates(
        self, 
        chunks: List[CodeChunk], 
        similarity_threshold: float = 0.95
    ) -> List[Tuple[CodeChunk, CodeChunk, float]]:
        """Find potential duplicate chunks"""
        duplicates = []
        
        for i, chunk1 in enumerate(chunks):
            if not chunk1.embedding:
                continue
                
            for chunk2 in chunks[i+1:]:
                if not chunk2.embedding:
                    continue
                
                similarity = self.calculate_similarity(chunk1, chunk2)
                if similarity >= similarity_threshold:
                    duplicates.append((chunk1, chunk2, similarity))
        
        return duplicates

    def get_chunk_summary(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Get summary information about a chunk"""
        summary = {
            "id": chunk.id,
            "type": chunk.chunk_type.value,
            "language": chunk.language,
            "file_path": chunk.file_path,
            "lines": f"{chunk.start_line}-{chunk.end_line}",
            "content_length": len(chunk.content),
            "has_embedding": chunk.embedding is not None,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
            "updated_at": chunk.updated_at.isoformat() if chunk.updated_at else None
        }
        
        # Add type-specific information
        if chunk.metadata:
            if chunk.chunk_type == ChunkType.FUNCTION:
                summary["function_name"] = chunk.metadata.get("function_name")
                summary["args"] = chunk.metadata.get("args", [])
            elif chunk.chunk_type == ChunkType.CLASS:
                summary["class_name"] = chunk.metadata.get("class_name")
                summary["methods"] = chunk.metadata.get("methods", [])
            elif chunk.chunk_type == ChunkType.METHOD:
                summary["class_name"] = chunk.metadata.get("class_name")
                summary["method_name"] = chunk.metadata.get("method_name")
        
        return summary
