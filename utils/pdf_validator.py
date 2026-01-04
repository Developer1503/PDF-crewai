"""
PDF Validator
Validates PDF quality and provides warnings before processing
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class PDFValidator:
    """
    Validates PDF files and provides quality assessment
    """
    
    # Size limits (in bytes)
    WARNING_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Page limits
    WARNING_PAGES = 100
    MAX_PAGES = 500
    
    def __init__(self):
        self.validation_history = []
    
    def validate_pdf(self, file_path: str, file_size: int, text_sample: str = None) -> Dict:
        """
        Comprehensive PDF validation
        
        Returns:
            {
                'valid': bool,
                'warnings': List[str],
                'errors': List[str],
                'recommendations': List[str],
                'metadata': Dict,
                'estimated_processing_time': int (seconds)
            }
        """
        warnings = []
        errors = []
        recommendations = []
        
        # Size validation
        if file_size > self.MAX_SIZE:
            errors.append(f"File too large ({file_size / (1024*1024):.1f}MB). Maximum is {self.MAX_SIZE / (1024*1024):.0f}MB")
        elif file_size > self.WARNING_SIZE:
            warnings.append(f"Large file detected ({file_size / (1024*1024):.1f}MB). Processing may take 2-3 minutes")
            recommendations.append("Consider splitting the document for faster processing")
        
        # Text extraction test
        if text_sample is not None:
            text_quality = self._assess_text_quality(text_sample)
            
            if text_quality['is_scanned']:
                warnings.append("This appears to be a scanned PDF with limited text extraction")
                recommendations.append("Text extraction may be incomplete. Consider using OCR")
            
            if text_quality['has_tables']:
                warnings.append("Document contains tables - extraction may not preserve formatting")
            
            if text_quality['language'] != 'english':
                warnings.append(f"Document appears to be in {text_quality['language']}")
        
        # Estimate processing time
        estimated_time = self._estimate_processing_time(file_size)
        
        # Determine validity
        valid = len(errors) == 0
        
        result = {
            'valid': valid,
            'warnings': warnings,
            'errors': errors,
            'recommendations': recommendations,
            'metadata': {
                'file_size_mb': file_size / (1024 * 1024),
                'estimated_processing_time': estimated_time
            },
            'estimated_processing_time': estimated_time
        }
        
        # Log validation
        self.validation_history.append({
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'result': result
        })
        
        return result
    
    def _assess_text_quality(self, text_sample: str) -> Dict:
        """Assess quality of extracted text"""
        # Check if scanned (very few words extracted)
        word_count = len(text_sample.split())
        is_scanned = word_count < 50 and len(text_sample) < 200
        
        # Check for tables (common table indicators)
        table_indicators = ['|', '─', '┌', '┐', '└', '┘', '├', '┤']
        has_tables = any(indicator in text_sample for indicator in table_indicators)
        
        # Simple language detection (very basic)
        english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'for']
        english_count = sum(1 for word in english_words if word in text_sample.lower())
        language = 'english' if english_count >= 3 else 'other'
        
        return {
            'is_scanned': is_scanned,
            'has_tables': has_tables,
            'language': language,
            'word_count': word_count
        }
    
    def _estimate_processing_time(self, file_size: int) -> int:
        """Estimate processing time in seconds"""
        # Rough estimation: 1MB = 5 seconds
        mb_size = file_size / (1024 * 1024)
        return int(mb_size * 5)
    
    def estimate_token_cost(self, text: str) -> Dict:
        """
        Estimate token cost for processing the document
        
        Returns:
            {
                'estimated_tokens': int,
                'cost_tier': str ('low', 'medium', 'high'),
                'warnings': List[str]
            }
        """
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(text) // 4
        
        warnings = []
        
        if estimated_tokens > 100000:
            cost_tier = 'high'
            warnings.append("Very large document - will consume significant API quota")
            warnings.append("Consider using 'Quick Analysis' mode")
        elif estimated_tokens > 50000:
            cost_tier = 'medium'
            warnings.append("Medium-sized document - moderate API usage expected")
        else:
            cost_tier = 'low'
        
        return {
            'estimated_tokens': estimated_tokens,
            'cost_tier': cost_tier,
            'warnings': warnings
        }


class DocumentAnalyzer:
    """
    Analyzes document type and extracts metadata
    """
    
    DOCUMENT_TYPES = {
        'legal_contract': {
            'keywords': ['whereas', 'hereby', 'indemnification', 'termination', 'agreement', 'party', 'clause'],
            'patterns': [r'article \d+', r'section \d+\.\d+', r'exhibit [a-z]'],
            'suggestions': [
                "What are the payment terms?",
                "List all key dates and deadlines",
                "What are the termination clauses?",
                "Who are the parties to this agreement?"
            ]
        },
        'research_paper': {
            'keywords': ['abstract', 'methodology', 'conclusion', 'references', 'hypothesis', 'results'],
            'patterns': [r'doi:', r'arxiv:', r'\d{4}\s+[A-Z][a-z]+'],
            'suggestions': [
                "Summarize the methodology",
                "What are the key findings?",
                "What are the limitations?",
                "Who are the authors?"
            ]
        },
        'financial_report': {
            'keywords': ['revenue', 'fiscal year', 'balance sheet', 'income statement', 'assets', 'liabilities'],
            'patterns': [r'\$[\d,]+', r'Q[1-4]\s+\d{4}', r'FY\s*\d{4}'],
            'suggestions': [
                "What are the revenue trends?",
                "List risk factors",
                "Compare year-over-year performance",
                "What are the key financial metrics?"
            ]
        },
        'technical_manual': {
            'keywords': ['installation', 'configuration', 'troubleshooting', 'specifications', 'requirements'],
            'patterns': [r'step \d+', r'figure \d+', r'table \d+'],
            'suggestions': [
                "What are the installation steps?",
                "List troubleshooting procedures",
                "What are the system requirements?",
                "Explain the configuration process"
            ]
        },
        'user_manual': {
            'keywords': ['instructions', 'warning', 'caution', 'safety', 'operation', 'maintenance'],
            'patterns': [r'chapter \d+', r'section \d+'],
            'suggestions': [
                "What are the safety warnings?",
                "How do I operate this?",
                "What maintenance is required?",
                "What are the troubleshooting steps?"
            ]
        }
    }
    
    def __init__(self):
        pass
    
    def detect_document_type(self, text: str) -> Dict:
        """
        Detect document type based on content analysis
        
        Returns:
            {
                'type': str,
                'confidence': float (0-1),
                'suggestions': List[str],
                'metadata': Dict
            }
        """
        text_lower = text.lower()
        scores = {}
        
        for doc_type, config in self.DOCUMENT_TYPES.items():
            score = 0
            
            # Score based on keywords
            for keyword in config['keywords']:
                if keyword in text_lower:
                    score += 1
            
            # Score based on patterns
            for pattern in config['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 2
            
            scores[doc_type] = score
        
        # Find best match
        if not scores or max(scores.values()) == 0:
            return {
                'type': 'general',
                'confidence': 0.5,
                'suggestions': [
                    "Summarize this document",
                    "What is the main topic?",
                    "List the key points"
                ],
                'metadata': {}
            }
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Calculate confidence (normalize score)
        confidence = min(1.0, max_score / 10)
        
        return {
            'type': best_type,
            'confidence': confidence,
            'suggestions': self.DOCUMENT_TYPES[best_type]['suggestions'],
            'metadata': {
                'scores': scores
            }
        }
    
    def extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata from document
        
        Returns:
            {
                'dates': List[str],
                'entities': Dict,
                'key_sections': List[str],
                'statistics': Dict
            }
        """
        # Extract dates
        dates = self._extract_dates(text)
        
        # Extract entities (companies, people)
        entities = self._extract_entities(text)
        
        # Extract key sections
        key_sections = self._extract_sections(text)
        
        # Calculate statistics
        statistics = {
            'word_count': len(text.split()),
            'char_count': len(text),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'estimated_read_time_minutes': len(text.split()) // 200  # Average reading speed
        }
        
        return {
            'dates': dates,
            'entities': entities,
            'key_sections': key_sections,
            'statistics': statistics
        }
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'[A-Z][a-z]+ \d{1,2},? \d{4}',  # Month DD, YYYY
            r'\d{1,2} [A-Z][a-z]+ \d{4}'  # DD Month YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))[:20]  # Return unique dates, max 20
    
    def _extract_entities(self, text: str) -> Dict:
        """Extract named entities (basic approach)"""
        # Extract potential company names (capitalized words followed by Inc, Corp, LLC, etc.)
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd|Limited|Corporation)\b'
        companies = list(set(re.findall(company_pattern, text)))
        
        # Extract potential person names (Title + Name pattern)
        person_pattern = r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        people = list(set(re.findall(person_pattern, text)))
        
        return {
            'companies': companies[:10],  # Max 10
            'people': people[:10]  # Max 10
        }
    
    def _extract_sections(self, text: str) -> List[str]:
        """Extract section headings"""
        # Look for common section patterns
        section_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS lines
            r'^(\d+\.\s+[A-Z].+)$',  # Numbered sections
            r'^(SECTION \d+.+)$',  # "SECTION X" pattern
            r'^(ARTICLE \d+.+)$'  # "ARTICLE X" pattern
        ]
        
        sections = []
        for line in text.split('\n'):
            line = line.strip()
            for pattern in section_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    sections.append(match.group(1))
                    break
        
        return sections[:15]  # Max 15 sections
    
    def generate_document_fingerprint(self, text: str, filename: str) -> Dict:
        """
        Generate comprehensive document fingerprint
        
        This is shown to user immediately upon upload
        """
        doc_type_info = self.detect_document_type(text)
        metadata = self.extract_metadata(text)
        
        # Find next important date
        next_date = None
        if metadata['dates']:
            # This is simplified - in production, parse and compare dates
            next_date = metadata['dates'][0] if metadata['dates'] else None
        
        return {
            'filename': filename,
            'type': doc_type_info['type'].replace('_', ' ').title(),
            'confidence': doc_type_info['confidence'],
            'length': f"{metadata['statistics']['word_count']:,} words",
            'pages_estimate': metadata['statistics']['word_count'] // 300,  # ~300 words per page
            'read_time': f"{metadata['statistics']['estimated_read_time_minutes']} min",
            'language': 'English',  # Simplified
            'key_dates': metadata['dates'][:5],
            'next_important_date': next_date,
            'entities': metadata['entities'],
            'sections': metadata['key_sections'][:5],
            'suggested_questions': doc_type_info['suggestions']
        }
