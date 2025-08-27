# Sophia AI Agentic Utilities
# ================================
# Custom research tools and utilities for enhanced agentic capabilities

import logging
from typing import Dict, List, Optional, Any, Union
import asyncio
import httpx
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import pdfplumber
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import redis
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class SophiaAgentTools:
    """Collection of custom research tools for Sophia AI agents"""

    @staticmethod
    def PerplexitySearch(api_key: str):
        """Create Perplexity AI search tool"""
        from agno.tools.perplexity import PerplexityTools
        return PerplexityTools(api_key=api_key)

    @staticmethod
    def GoogleCustomSearch(api_key: str):
        """Create Google Custom Search tool"""
        from agno.tools.serper import SerperTools
        return SerperTools(api_key=api_key)

    @staticmethod
    def ApifyScraping(api_token: str):
        """Create Apify web scraping tool"""
        try:
            import apify_client

            class ApifyWebScraper:
                def __init__(self, token: str):
                    self.client = apify_client.ApifyClient(token)

                def scrape_url(self, url: str, max_pages: int = 10) -> Dict[str, Any]:
                    """Scrape a website using Apify Web Scraper actor"""
                    try:
                        input_data = {
                            "startUrl": url,
                            "maxPages": max_pages,
                            "keepUrlFragments": False,
                            "enqueueLinks": True,
                        }

                        run = self.client.actor("apidojo/web-scraper").call(run_input=input_data)

                        # Get the dataset
                        dataset = self.client.dataset(run["defaultDatasetId"]).list_items()

                        results = []
                        for item in dataset:
                            results.append({
                                "url": item.get("url"),
                                "title": item.get("title", ""),
                                "content": item.get("text", ""),
                                "timestamp": item.get("loadedAt")
                            })

                        return {
                            "success": True,
                            "data": results,
                            "pages_scraped": len(results)
                        }

                    except Exception as e:
                        logger.error(f"Apify scraping error: {str(e)}")
                        return {"success": False, "error": str(e)}

            return ApifyWebScraper(api_token)

        except ImportError:
            logger.warning("apify-client not installed")
            return None

    @staticmethod
    def ZenRowsScraping(api_key: str):
        """Create ZenRows web scraping tool"""
        try:
            import zenrows

            class ZenRowsScraper:
                def __init__(self, api_key: str):
                    self.api_key = api_key

                def scrape_url(self, url: str, js_render: bool = True) -> Dict[str, Any]:
                    """Scrape with ZenRows premium scraping capabilities"""
                    try:
                        from zenrows import ZenRows
                        client = ZenRows(self.api_key)

                        params = {
                            "block_resources": "image,media,font",
                            "js_render": js_render,
                            "premium_proxy": True,
                        }

                        response = client.scrape(url, **params)

                        return {
                            "success": True,
                            "url": url,
                            "content": response.get("content", ""),
                            "title": response.get("title", ""),
                            "status_code": response.get("status_code")
                        }

                    except Exception as e:
                        logger.error(f"ZenRows scraping error: {str(e)}")
                        return {"success": False, "error": str(e)}

            return ZenRowsScraper(api_key)

        except ImportError:
            logger.warning("zenrows not installed")
            return None

    @staticmethod
    def BrightDataScraping(api_key: str):
        """Create BrightData enterprise scraping tool"""
        try:
            class BrightDataScraper:
                def __init__(self, api_key: str):
                    self.api_key = api_key
                    self.base_url = "https://brd.superproxy.io:22225"

                def scrape_url(self, url: str) -> Dict[str, Any]:
                    """Scrape with BrightData enterprise proxy network"""
                    try:
                        proxies = {
                            'http': f'http://{self.api_key}:loffx_rotation@main_domain/brd.superproxy.io:22225',
                            'https': f'https://{self.api_key}:loffx_rotation@main_domain/brd.superproxy.io:22225'
                        }

                        response = requests.get(url, proxies=proxies, verify=False, timeout=30)

                        return {
                            "success": True,
                            "url": url,
                            "content": response.text,
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "timestamp": datetime.now().isoformat()
                        }

                    except Exception as e:
                        logger.error(f"BrightData scraping error: {str(e)}")
                        return {"success": False, "error": str(e)}

            return BrightDataScraper(api_key)

        except Exception as e:
            logger.error(f"BrightData setup error: {str(e)}")
            return None

    @staticmethod
    def ExaAISearch(api_key: str):
        """Create Exa AI search with memory tool"""
        try:
            import exa_py

            class ExaAISearch:
                def __init__(self, api_key: str):
                    self.client = exa_py.Exa(api_key)

                def search_and_explain(self, query: str, num_results: int = 10) -> Dict[str, Any]:
                    """Search with Exa's AI-powered explanation"""
                    try:
                        response = self.client.search_and_contents(
                            query,
                            num_results=num_results,
                            use_autoprompt=True,
                            include_domains=None
                        )

                        results = []
                        for result in response.results:
                            results.append({
                                "title": result.title,
                                "url": result.url,
                                "content": result.content[:2000] if result.content else "",
                                "score": getattr(result, "score", 0),
                                "published_date": getattr(result, "published_date", None)
                            })

                        return {
                            "success": True,
                            "query": query,
                            "results": results,
                            "total_results": len(results),
                            "autoprompt_used": response.autoprompt
                        }

                    except Exception as e:
                        logger.error(f"Exa AI search error: {str(e)}")
                        return {"success": False, "error": str(e)}

            return ExaAISearch(api_key)

        except ImportError:
            logger.warning("exa-py not installed")
            return None

    @staticmethod
    def CustomResearchTools():
        """Collection of custom research utilities"""
        return _CustomResearchTools()


class _CustomResearchTools:
    """Custom research tools implementation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        try:
            # Simple keyword extraction using frequency and importance
            words = re.findall(r'\b\w+\b', text.lower())
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

            word_freq = {}
            for word in words:
                if word not in stop_words and len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Sort by frequency and return top keywords
            sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [kw[0] for kw in sorted_keywords[:max_keywords]]

        except Exception as e:
            self.logger.error(f"Keyword extraction error: {str(e)}")
            return []

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment in text"""
        try:
            # Simple sentiment analysis based on word lists
            positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'love', 'happy', 'positive'}
            negative_words = {'bad', 'poor', 'terrible', 'awful', 'worst', 'hate', 'sad', 'negative', 'worst'}

            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)

            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words == 0:
                sentiment_score = 0
            else:
                sentiment_score = (positive_count - negative_count) / total_sentiment_words

            sentiment_label = "neutral"
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"

            return {
                "sentiment_score": sentiment_score,
                "label": sentiment_label,
                "positive_words": positive_count,
                "negative_words": negative_count,
                "confidence": abs(sentiment_score)
            }

        except Exception as e:
            self.logger.error(f"Sentiment analysis error: {str(e)}")
            return {"error": str(e)}

    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            # Simple language detection based on common words
            text_lower = text.lower()

            chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
            if chinese_chars:
                return "zh"

            cyrillic_chars = re.findall(r'[\u0400-\u04ff]', text)
            if cyrillic_chars:
                return "ru"

            if 'the' in text_lower and 'and' in text_lower and 'is' in text_lower:
                return "en"

            if 'und' in text_lower and 'der' in text_lower and 'die' in text_lower:
                return "de"

            if 'et' in text_lower and 'le' in text_lower and 'est' in text_lower:
                return "fr"

            if 'es' in text_lower and 'el' in text_lower and 'la' in text_lower:
                return "es"

            return "unknown"

        except Exception as e:
            self.logger.error(f"Language detection error: {str(e)}")
            return "error"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        try:
            entities = {
                "persons": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "emails": [],
                "urls": []
            }

            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            entities["emails"] = re.findall(email_pattern, text)

            # Extract URLs
            url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?'
            entities["urls"] = re.findall(url_pattern, text)

            # Extract dates (simple patterns)
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',     # YYYY/MM/DD
                r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}\b'  # DD Mon YYYY
            ]

            for pattern in date_patterns:
                entities["dates"].extend(re.findall(pattern, text))

            # Remove duplicates
            for key in entities:
                entities[key] = list(set(entities[key]))

            return entities

        except Exception as e:
            self.logger.error(f"Entity extraction error: {str(e)}")
            return {"error": str(e)}

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Create a summary of text"""
        try:
            # Simple extractive summarization using sentence scoring
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

            if not sentences:
                return text[:max_length] + "..." if len(text) > max_length else text

            # Score sentences based on position and length
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                position_boost = ((len(sentences) - i) / len(sentences)) * 0.3
                length_boost = min(len(sentence) / 200, 1) * 0.3
                word_importance = sum(1 for word in sentence.lower().split() if len(word) > 6) / len(sentence.split()) * 0.4
                score = position_boost + length_boost + word_importance
                scored_sentences.append((score, sentence))

            # Select top sentences
            scored_sentences.sort(reverse=True)
            summary_sentences = []
            current_length = 0

            for _, sentence in scored_sentences:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break

            return ". ".join(summary_sentences) + "."

        except Exception as e:
            self.logger.error(f"Text summarization error: {str(e)}")
            return text[:max_length] + "..." if len(text) > max_length else text

    def calculate_readability_score(self, text: str) -> Dict[str, Any]:
        """Calculate readability scores for text"""
        try:
            sentences = len(re.findall(r'[.!?]+', text))
            words = len(text.split())
            syllables = sum(1 for word in text.split() for vowel in set(word.lower()) if vowel in 'aeiou')

            if sentences == 0 or words == 0:
                return {"flesch_score": 0, "grade_level": "Unknown", "error": "Insufficient text"}

            # Flesch-Kincaid grade level
            fk_score = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

            # Flesch reading ease (inverted scale)
            reading_ease = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

            return {
                "flesch_kincaid_grade": round(fk_score, 1),
                "reading_ease_score": round(reading_ease, 1),
                "sentence_count": sentences,
                "word_count": words,
                "syllable_count": syllables,
                "avg_words_per_sentence": round(words / sentences, 1) if sentences > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Readability calculation error: {str(e)}")
            return {"error": str(e)}

    def create_document_hash(self, content: str) -> str:
        """Create a hash for document deduplication"""
        try:
            # Normalize content for hashing
            normalized = re.sub(r'\s+', ' ', content.strip().lower())
            return hashlib.sha256(normalized.encode()).hexdigest()[:16]

        except Exception as e:
            self.logger.error(f"Document hashing error: {str(e)}")
            return hashlib.sha256(str(content).encode()).hexdigest()[:16]


class ContentProcessor:
    """Advanced content processing utilities for research"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_articles(self, html_content: str, url: str = None) -> List[Dict[str, Any]]:
        """Extract articles and structured content from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            articles = []

            # Try to find article content
            article_selectors = [
                'article',
                '[class*="article"]',
                '[class*="post"]',
                '[class*="content"]',
                'main',
                '.main-content',
                '#main-content'
            ]

            for selector in article_selectors:
                content = soup.select_one(selector)
                if content:
                    article = self._extract_article_data(content, url)
                    if article and len(article.get('content', '')) > 100:
                        articles.append(article)
                        break

            return articles

        except Exception as e:
            self.logger.error(f"Article extraction error: {str(e)}")
            return []

    def _extract_article_data(self, soup_element, url: str = None) -> Dict[str, Any]:
        """Extract data from soup element"""
        try:
            # Extract title
            title_selectors = ['h1', '.title', '.headline', '[class*="title"]']
            title = ""
            for selector in title_selectors:
                title_element = soup_element.select_one(selector)
                if title_element:
                    title = title_element.get_text().strip()
                    break

            # Extract content
            content_text = soup_element.get_text(separator=' ', strip=True)

            # Extract metadata
            meta_tags = soup_element.select('meta')
            metadata = {}
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property')
                if name:
                    metadata[name] = meta.get('content', '')

            # Extract publication date
            pub_date = None
            date_selectors = ['time', '[datetime]', '[class*="date"]', '[class*="published"]']
            for selector in date_selectors:
                date_element = soup_element.select_one(selector)
                if date_element:
                    datetime_attr = date_element.get('datetime')
                    if datetime_attr:
                        try:
                            pub_date = datetime.fromisoformat(datetime_attr).date().isoformat()
                            break
                        except:
                            pass

            return {
                "title": title,
                "content": content_text,
                "url": url,
                "publication_date": pub_date,
                "metadata": metadata,
                "word_count": len(content_text.split()) if content_text else 0,
                "extract_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Article data extraction error: {str(e)}")
            return {"error": str(e)}

    def process_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Extract and process content from PDF files"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                metadata = {}
                pages = []

                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                        pages.append({"page_number": page.page_number, "content": text})

                # Extract title from first few lines
                lines = full_text.split('\n')[:10]
                title_candidates = [line.strip() for line in lines if len(line.strip()) > 10]
                title = title_candidates[0] if title_candidates else f"PDF Document: {Path(pdf_path).name}"

                return {
                    "title": title,
                    "content": full_text,
                    "pages": pages,
                    "total_pages": len(pdf.pages),
                    "pdf_path": str(pdf_path),
                    "word_count": len(full_text.split()),
                    "processing_timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"PDF processing error: {str(e)}")
            return {"error": str(e), "pdf_path": str(pdf_path)}

    def batch_process_documents(self, document_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents in batch"""
        try:
            results = {}
            processed_count = 0
            error_count = 0

            for path in document_paths:
                try:
                    if path LOWER(".pdf"):
                        results[path] = self.process_pdf_content(path)
                    elif path.lower().endswith('.html'):
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        results[path] = self.extract_articles(content, url=path)[0] if self.extract_articles(content, url=path) else {"error": "No content found"}
                    else:
                        # Try to read as text
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        results[path] = {
                            "content": content,
                            "word_count": len(content.split()),
                            "path": path
                        }

                    processed_count += 1

                except Exception as e:
                    self.logger.error(f"Error processing {path}: {str(e)}")
                    results[path] = {"error": str(e), "path": path}
                    error_count += 1

            return {
                "results": results,
                "processed_count": processed_count,
                "error_count": error_count,
                "batch_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            return {"error": str(e)}


# Convenience functions
def create_custom_toolkit() -> Dict[str, Any]:
    """Create a comprehensive toolkit for agents"""
    tools = SophiaAgentTools.CustomResearchTools()
    return {
        "keyword_extractor": tools.extract_keywords,
        "sentiment_analyzer": tools.analyze_sentiment,
        "language_detector": tools.detect_language,
        "entity_extractor": tools.extract_entities,
        "text_summarizer": tools.summarize_text,
        "readability_scorer": tools.calculate_readability_score,
        "document_hasher": tools.create_document_hash
    }


def create_content_processor() -> ContentProcessor:
    """Create content processing instance"""
    return ContentProcessor()
