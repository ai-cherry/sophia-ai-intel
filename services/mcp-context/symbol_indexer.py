#!/usr/bin/env python3
"""
Symbol Indexer for Sophia AI Context MCP
Uses tree-sitter for stable code parsing and chunk ID generation
Generates embeddings for semantic search
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import uuid

import tree_sitter_python as tspython
import tree_sitter_typescript as tstyped
import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser, Node
import openai
import asyncpg
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SymbolInfo:
    """Information about a code symbol"""
    symbol_type: str
    name: str
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    content: str
    documentation: str
    chunk_id: str
    dependencies: List[str]
    complexity_score: float

@dataclass
class IndexingStats:
    """Statistics for indexing operation"""
    files_processed: int = 0
    symbols_extracted: int = 0
    embeddings_generated: int = 0
    processing_time_ms: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class LanguageConfig:
    """Configuration for supported languages"""
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'extensions': ['.py'],
            'language': Language(tspython.language()),
            'symbol_queries': [
                # Functions
                '(function_definition name: (identifier) @function.name) @function.definition',
                # Classes
                '(class_definition name: (identifier) @class.name) @class.definition',
                # Methods (functions inside classes)
                '(class_definition body: (block (function_definition name: (identifier) @method.name))) @method.definition',
                # Variables at module level
                '(module (expression_statement (assignment left: (identifier) @variable.name))) @variable.definition',
                # Constants (uppercase variables)
                '(module (expression_statement (assignment left: (identifier) @constant.name))) @constant.definition',
                # Imports
                '(import_statement) @import.statement',
                '(import_from_statement) @import.statement'
            ]
        },
        'typescript': {
            'extensions': ['.ts', '.tsx'],
            'language': Language(tstyped.language()),
            'symbol_queries': [
                # Functions
                '(function_declaration name: (identifier) @function.name) @function.definition',
                # Arrow functions assigned to variables
                '(variable_declaration (variable_declarator name: (identifier) @function.name value: (arrow_function))) @function.definition',
                # Classes
                '(class_declaration name: (type_identifier) @class.name) @class.definition',
                # Interfaces
                '(interface_declaration name: (type_identifier) @interface.name) @interface.definition',
                # Type aliases
                '(type_alias_declaration name: (type_identifier) @type.name) @type.definition',
                # Methods
                '(class_declaration body: (class_body (method_definition name: (property_identifier) @method.name))) @method.definition',
                # Variables/Constants
                '(variable_declaration (variable_declarator name: (identifier) @variable.name)) @variable.definition',
                # Enums
                '(enum_declaration name: (identifier) @enum.name) @enum.definition'
            ]
        },
        'javascript': {
            'extensions': ['.js', '.jsx'],
            'language': Language(tsjs.language()),
            'symbol_queries': [
                # Functions
                '(function_declaration name: (identifier) @function.name) @function.definition',
                # Arrow functions
                '(variable_declaration (variable_declarator name: (identifier) @function.name value: (arrow_function))) @function.definition',
                # Classes
                '(class_declaration name: (identifier) @class.name) @class.definition',
                # Methods
                '(class_declaration body: (class_body (method_definition name: (property_identifier) @method.name))) @method.definition',
                # Variables
                '(variable_declaration (variable_declarator name: (identifier) @variable.name)) @variable.definition'
            ]
        }
    }

class SymbolIndexer:
    """Indexes code symbols with tree-sitter for stable parsing"""
    
    def __init__(self, 
                 db_url: str,
                 openai_api_key: str,
                 project_root: str,
                 embedding_model: str = "text-embedding-3-small",
                 embedding_dimensions: int = 1536):
        self.db_url = db_url
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.project_root = Path(project_root)
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        
        # Initialize parsers for each language
        self.parsers = {}
        for lang, config in LanguageConfig.SUPPORTED_LANGUAGES.items():
            parser = Parser()
            parser.set_language(config['language'])
            self.parsers[lang] = parser
    
    async def get_db_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        return await asyncpg.connect(self.db_url)
    
    def get_language_for_file(self, file_path: Path) -> Optional[str]:
        """Determine language based on file extension"""
        suffix = file_path.suffix.lower()
        for lang, config in LanguageConfig.SUPPORTED_LANGUAGES.items():
            if suffix in config['extensions']:
                return lang
        return None
    
    def generate_chunk_id(self, project_id: str, file_path: str, symbol_name: str, start_line: int) -> str:
        """Generate stable chunk ID for symbol"""
        content = f"{project_id}|{file_path}|{symbol_name}|{start_line}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def extract_documentation(self, node: Node, source_code: bytes) -> str:
        """Extract documentation/comments for a symbol"""
        # Look for docstrings or comments near the symbol
        documentation = ""
        
        # For Python, look for docstring as first statement
        if node.type in ['function_definition', 'class_definition']:
            body = node.child_by_field_name('body')
            if body and body.children:
                first_stmt = body.children[0]
                if first_stmt.type == 'expression_statement':
                    expr = first_stmt.children[0]
                    if expr.type == 'string' and expr.children:
                        # This is likely a docstring
                        documentation = expr.text.decode('utf-8').strip('"\'')
        
        # Look for comments immediately before the symbol
        start_line = node.start_point[0]
        lines = source_code.decode('utf-8').split('\n')
        
        comment_lines = []
        for i in range(start_line - 1, -1, -1):
            if i < len(lines):
                line = lines[i].strip()
                if line.startswith('#') or line.startswith('//') or line.startswith('/**') or line.startswith('*'):
                    comment_lines.insert(0, line)
                elif line == '':
                    continue  # Skip empty lines
                else:
                    break  # Stop at first non-comment, non-empty line
        
        if comment_lines:
            comment_doc = '\n'.join(comment_lines)
            if documentation:
                documentation = f"{comment_doc}\n\n{documentation}"
            else:
                documentation = comment_doc
        
        return documentation.strip()
    
    def calculate_complexity_score(self, node: Node, source_code: bytes) -> float:
        """Calculate a simple complexity score for the symbol"""
        # Basic cyclomatic complexity approximation
        complexity = 1.0  # Base complexity
        
        def count_complexity_nodes(n: Node) -> int:
            count = 0
            complexity_types = {
                'if_statement', 'while_statement', 'for_statement', 'try_statement',
                'except_clause', 'switch_statement', 'case_clause', 'conditional_expression'
            }
            
            if n.type in complexity_types:
                count += 1
            
            for child in n.children:
                count += count_complexity_nodes(child)
            
            return count
        
        complexity += count_complexity_nodes(node)
        
        # Factor in size (lines of code)
        line_count = node.end_point[0] - node.start_point[0] + 1
        if line_count > 50:
            complexity *= 1.2
        if line_count > 100:
            complexity *= 1.5
        
        return min(complexity, 10.0)  # Cap at 10.0
    
    def extract_dependencies(self, node: Node, source_code: bytes, language: str) -> List[str]:
        """Extract dependencies (other symbols this symbol references)"""
        dependencies = []
        
        def extract_identifiers(n: Node):
            if n.type == 'identifier':
                name = n.text.decode('utf-8')
                if name not in ['self', 'this', 'super'] and len(name) > 1:
                    dependencies.append(name)
            
            for child in n.children:
                extract_identifiers(child)
        
        extract_identifiers(node)
        
        # Remove duplicates and the symbol's own name
        symbol_name = self.get_symbol_name(node, source_code)
        return list(set(dep for dep in dependencies if dep != symbol_name))
    
    def get_symbol_name(self, node: Node, source_code: bytes) -> str:
        """Extract symbol name from node"""
        # Try to find name field
        name_node = node.child_by_field_name('name')
        if name_node:
            return name_node.text.decode('utf-8')
        
        # Fallback: look for identifier children
        for child in node.children:
            if child.type in ['identifier', 'property_identifier', 'type_identifier']:
                return child.text.decode('utf-8')
        
        return 'unknown'
    
    def get_qualified_name(self, node: Node, source_code: bytes, file_path: str) -> str:
        """Generate qualified name including namespace/class context"""
        symbol_name = self.get_symbol_name(node, source_code)
        
        # Walk up the tree to find containing classes/namespaces
        parent = node.parent
        qualifiers = []
        
        while parent:
            if parent.type in ['class_definition', 'class_declaration']:
                class_name = self.get_symbol_name(parent, source_code)
                qualifiers.insert(0, class_name)
            elif parent.type in ['namespace_declaration', 'module']:
                # Handle namespaces if present
                namespace_name = self.get_symbol_name(parent, source_code)
                if namespace_name != 'unknown':
                    qualifiers.insert(0, namespace_name)
            parent = parent.parent
        
        # Add file name as base qualifier
        file_base = Path(file_path).stem
        qualifiers.insert(0, file_base)
        
        qualifiers.append(symbol_name)
        return '.'.join(qualifiers)
    
    def get_symbol_type(self, node: Node) -> str:
        """Determine symbol type from AST node"""
        type_mapping = {
            'function_definition': 'function',
            'function_declaration': 'function', 
            'class_definition': 'class',
            'class_declaration': 'class',
            'interface_declaration': 'interface',
            'type_alias_declaration': 'type',
            'enum_declaration': 'enum',
            'method_definition': 'method',
            'variable_declaration': 'variable',
            'variable_declarator': 'variable'
        }
        
        symbol_type = type_mapping.get(node.type, 'unknown')
        
        # Special handling for constants (uppercase variables)
        if symbol_type == 'variable':
            name = self.get_symbol_name(node, b'')
            if name.isupper():
                return 'constant'
        
        return symbol_type
    
    async def parse_file(self, file_path: Path, language: str, project_id: str) -> Tuple[List[SymbolInfo], List[str]]:
        """Parse a single file and extract symbols"""
        symbols = []
        errors = []
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            # Parse with tree-sitter
            parser = self.parsers[language]
            tree = parser.parse(source_code)
            
            # Get language configuration
            lang_config = LanguageConfig.SUPPORTED_LANGUAGES[language]
            
            # Process each query pattern
            for query_text in lang_config['symbol_queries']:
                try:
                    query = lang_config['language'].query(query_text)
                    captures = query.captures(tree.root_node)
                    
                    for node, capture_name in captures:
                        if capture_name.endswith('.definition'):
                            try:
                                symbol_info = await self.extract_symbol_info(
                                    node, source_code, file_path, language, project_id
                                )
                                if symbol_info:
                                    symbols.append(symbol_info)
                            except Exception as e:
                                error_msg = f"Error extracting symbol from {file_path}:{node.start_point[0]}: {str(e)}"
                                errors.append(error_msg)
                                logger.warning(error_msg)
                
                except Exception as e:
                    error_msg = f"Error processing query '{query_text[:50]}...' in {file_path}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
        
        except Exception as e:
            error_msg = f"Error parsing file {file_path}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return symbols, errors
    
    async def extract_symbol_info(self, node: Node, source_code: bytes, 
                                  file_path: Path, language: str, project_id: str) -> Optional[SymbolInfo]:
        """Extract detailed information about a symbol"""
        try:
            name = self.get_symbol_name(node, source_code)
            if name == 'unknown' or len(name) < 2:
                return None
            
            symbol_type = self.get_symbol_type(node)
            qualified_name = self.get_qualified_name(node, source_code, str(file_path))
            
            # Get position information
            start_line = node.start_point[0] + 1  # Convert to 1-based
            end_line = node.end_point[0] + 1
            
            # Extract content
            content = node.text.decode('utf-8')
            
            # Extract documentation
            documentation = self.extract_documentation(node, source_code)
            
            # Generate stable chunk ID
            rel_path = str(file_path.relative_to(self.project_root))
            chunk_id = self.generate_chunk_id(project_id, rel_path, name, start_line)
            
            # Extract dependencies
            dependencies = self.extract_dependencies(node, source_code, language)
            
            # Calculate complexity
            complexity_score = self.calculate_complexity_score(node, source_code)
            
            return SymbolInfo(
                symbol_type=symbol_type,
                name=name,
                qualified_name=qualified_name,
                file_path=rel_path,
                start_line=start_line,
                end_line=end_line,
                language=language,
                content=content,
                documentation=documentation,
                chunk_id=chunk_id,
                dependencies=dependencies,
                complexity_score=complexity_score
            )
        
        except Exception as e:
            logger.error(f"Error extracting symbol info: {str(e)}")
            return None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI API"""
        try:
            # Prepare text for embedding (combine content and documentation)
            embedding_text = text[:8000]  # Limit text length
            
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=embedding_text,
                dimensions=self.embedding_dimensions
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def store_symbols(self, symbols: List[SymbolInfo], project_id: str, conn: asyncpg.Connection):
        """Store symbols in database with embeddings"""
        for symbol in symbols:
            try:
                # Generate embedding
                embedding_text = f"{symbol.content}\n\n{symbol.documentation}"
                embedding = await self.generate_embedding(embedding_text)
                
                # Store in database
                await conn.execute("""
                    INSERT INTO symbols (
                        project_id, symbol_type, name, qualified_name, file_path,
                        start_line, end_line, language, content, documentation,
                        chunk_id, embedding_vector, dependencies, complexity_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (project_id, chunk_id) DO UPDATE SET
                        symbol_type = EXCLUDED.symbol_type,
                        name = EXCLUDED.name,
                        qualified_name = EXCLUDED.qualified_name,
                        file_path = EXCLUDED.file_path,
                        start_line = EXCLUDED.start_line,
                        end_line = EXCLUDED.end_line,
                        language = EXCLUDED.language,
                        content = EXCLUDED.content,
                        documentation = EXCLUDED.documentation,
                        embedding_vector = EXCLUDED.embedding_vector,
                        dependencies = EXCLUDED.dependencies,
                        complexity_score = EXCLUDED.complexity_score,
                        last_modified = NOW()
                """, 
                project_id, symbol.symbol_type, symbol.name, symbol.qualified_name,
                symbol.file_path, symbol.start_line, symbol.end_line, symbol.language,
                symbol.content, symbol.documentation, symbol.chunk_id,
                embedding, json.dumps(symbol.dependencies), symbol.complexity_score)
            
            except Exception as e:
                logger.error(f"Error storing symbol {symbol.name}: {str(e)}")
    
    def discover_source_files(self, extensions: Set[str], exclude_patterns: Set[str] = None) -> List[Path]:
        """Discover all source files in project"""
        if exclude_patterns is None:
            exclude_patterns = {
                'node_modules', '.git', '__pycache__', '.pytest_cache',
                'dist', 'build', '.next', 'coverage', '.nyc_output',
                'venv', '.venv', 'env', '.env'
            }
        
        source_files = []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                # Check if file is in excluded directory
                if any(pattern in str(file_path) for pattern in exclude_patterns):
                    continue
                
                source_files.append(file_path)
        
        return sorted(source_files)
    
    async def index_project(self, project_name: str, index_type: str = 'full') -> IndexingStats:
        """Index entire project"""
        start_time = time.time()
        stats = IndexingStats()
        
        logger.info(f"Starting {index_type} index of project: {project_name}")
        
        try:
            conn = await self.get_db_connection()
            
            # Get or create project
            project_row = await conn.fetchrow(
                "SELECT id FROM projects WHERE name = $1", project_name
            )
            
            if not project_row:
                project_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO projects (id, name, repository_url, status)
                    VALUES ($1, $2, $3, 'active')
                """, project_id, project_name, str(self.project_root))
            else:
                project_id = str(project_row['id'])
            
            # Clear existing symbols if full index
            if index_type == 'full':
                await conn.execute("DELETE FROM symbols WHERE project_id = $1", project_id)
            
            # Collect all supported file extensions
            all_extensions = set()
            for config in LanguageConfig.SUPPORTED_LANGUAGES.values():
                all_extensions.update(config['extensions'])
            
            # Discover source files
            source_files = self.discover_source_files(all_extensions)
            logger.info(f"Found {len(source_files)} source files")
            
            # Create indexing statistics record
            index_stat_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO index_statistics (
                    id, project_id, index_type, status
                ) VALUES ($1, $2, $3, 'running')
            """, index_stat_id, project_id, index_type)
            
            # Process files
            for file_path in source_files:
                try:
                    language = self.get_language_for_file(file_path)
                    if not language:
                        continue
                    
                    logger.info(f"Processing {file_path} ({language})")
                    symbols, errors = await self.parse_file(file_path, language, project_id)
                    
                    if symbols:
                        await self.store_symbols(symbols, project_id, conn)
                        stats.symbols_extracted += len(symbols)
                    
                    if errors:
                        stats.errors.extend(errors)
                    
                    stats.files_processed += 1
                    
                    # Progress logging
                    if stats.files_processed % 10 == 0:
                        logger.info(f"Processed {stats.files_processed}/{len(source_files)} files, "
                                   f"extracted {stats.symbols_extracted} symbols")
                
                except Exception as e:
                    error_msg = f"Error processing file {file_path}: {str(e)}"
                    stats.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update statistics
            end_time = time.time()
            stats.processing_time_ms = int((end_time - start_time) * 1000)
            
            await conn.execute("""
                UPDATE index_statistics SET
                    symbols_processed = $1,
                    files_processed = $2,
                    processing_time_ms = $3,
                    errors_encountered = $4,
                    error_details = $5,
                    completed_at = NOW(),
                    status = 'completed'
                WHERE id = $6
            """, stats.symbols_extracted, stats.files_processed, stats.processing_time_ms,
                len(stats.errors), json.dumps(stats.errors), index_stat_id)
            
            await conn.close()
            
            logger.info(f"Indexing completed: {stats.files_processed} files, "
                       f"{stats.symbols_extracted} symbols, {len(stats.errors)} errors, "
                       f"{stats.processing_time_ms}ms")
        
        except Exception as e:
            error_msg = f"Critical error during indexing: {str(e)}"
            stats.errors.append(error_msg)
            logger.error(error_msg)
        
        return stats

# CLI interface for direct usage
async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Index code symbols for Sophia AI Context')
    parser.add_argument('--project-root', required=True, help='Root directory of project to index')
    parser.add_argument('--project-name', required=True, help='Name of the project')
    parser.add_argument('--db-url', required=True, help='PostgreSQL database URL')
    parser.add_argument('--openai-api-key', required=True, help='OpenAI API key for embeddings')
    parser.add_argument('--index-type', default='full', choices=['full', 'incremental'], 
                       help='Type of indexing to perform')
    
    args = parser.parse_args()
    
    indexer = SymbolIndexer(
        db_url=args.db_url,
        openai_api_key=args.openai_api_key,
        project_root=args.project_root
    )
    
    stats = await indexer.index_project(args.project_name, args.index_type)
    
    print(f"\nIndexing Results:")
    print(f"Files processed: {stats.files_processed}")
    print(f"Symbols extracted: {stats.symbols_extracted}")
    print(f"Processing time: {stats.processing_time_ms}ms")
    print(f"Errors: {len(stats.errors)}")
    
    if stats.errors:
        print("\nErrors encountered:")
        for error in stats.errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(stats.errors) > 10:
            print(f"  ... and {len(stats.errors) - 10} more errors")

if __name__ == "__main__":
    asyncio.run(main())