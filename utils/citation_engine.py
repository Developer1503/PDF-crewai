"""
Citation Engine
Extracts, verifies, and formats citations from LLM responses
"""

import re
from typing import Dict, List, Optional, Tuple


class CitationEngine:
    """
    Handles citation extraction, verification, and confidence scoring
    """
    
    CITATION_PROMPT_ADDITION = """
You MUST cite your sources for every claim. Format your response as follows:

**Answer:** [Your detailed response]

**Source:** Page [X], Section [Y] (or "Not in document" if using general knowledge)

**Confidence:** [High/Medium/Low]
- High: Direct quote from document
- Medium: Paraphrased from document
- Low: Inferred from context or general knowledge

**Quote:** "[Exact text from PDF if available]"

**Classification:** [DIRECT_QUOTE / PARAPHRASE / INFERENCE / GENERAL_KNOWLEDGE]

Always include page numbers when referencing the document. If information is not in the document, clearly state that.
"""
    
    def __init__(self):
        self.citation_cache = {}
    
    def enhance_system_prompt(self, original_prompt: str) -> str:
        """Add citation requirements to system prompt"""
        return original_prompt + "\n\n" + self.CITATION_PROMPT_ADDITION
    
    def extract_citations(self, response: str) -> Dict:
        """
        Extract citation information from LLM response
        
        Returns:
            {
                'answer': str,
                'source': str,
                'confidence': str,
                'quote': str,
                'classification': str,
                'page_numbers': List[int],
                'has_citation': bool
            }
        """
        # Initialize result
        result = {
            'answer': response,
            'source': 'Not specified',
            'confidence': 'Unknown',
            'quote': '',
            'classification': 'UNKNOWN',
            'page_numbers': [],
            'has_citation': False
        }
        
        # Extract answer
        answer_match = re.search(r'\*\*Answer:\*\*\s*(.+?)(?=\*\*Source:|$)', response, re.DOTALL | re.IGNORECASE)
        if answer_match:
            result['answer'] = answer_match.group(1).strip()
        
        # Extract source
        source_match = re.search(r'\*\*Source:\*\*\s*(.+?)(?=\*\*Confidence:|$)', response, re.DOTALL | re.IGNORECASE)
        if source_match:
            result['source'] = source_match.group(1).strip()
            result['has_citation'] = True
        
        # Extract confidence
        confidence_match = re.search(r'\*\*Confidence:\*\*\s*(\w+)', response, re.IGNORECASE)
        if confidence_match:
            result['confidence'] = confidence_match.group(1).strip()
        
        # Extract quote
        quote_match = re.search(r'\*\*Quote:\*\*\s*["\'](.+?)["\']', response, re.DOTALL | re.IGNORECASE)
        if quote_match:
            result['quote'] = quote_match.group(1).strip()
        
        # Extract classification
        class_match = re.search(r'\*\*Classification:\*\*\s*(\w+(?:_\w+)?)', response, re.IGNORECASE)
        if class_match:
            result['classification'] = class_match.group(1).strip().upper()
        
        # Extract page numbers
        result['page_numbers'] = self._extract_page_numbers(result['source'])
        
        return result
    
    def _extract_page_numbers(self, source_text: str) -> List[int]:
        """Extract page numbers from source citation"""
        page_numbers = []
        
        # Pattern: "Page 5", "page 5-7", "pages 5, 7, 9"
        patterns = [
            r'[Pp]age\s+(\d+)',
            r'[Pp]ages\s+([\d,\s-]+)',
            r'p\.?\s*(\d+)',
            r'pp\.?\s*([\d,\s-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, source_text)
            for match in matches:
                # Handle ranges like "5-7"
                if '-' in match:
                    start, end = match.split('-')
                    page_numbers.extend(range(int(start.strip()), int(end.strip()) + 1))
                # Handle comma-separated like "5, 7, 9"
                elif ',' in match:
                    page_numbers.extend([int(p.strip()) for p in match.split(',') if p.strip().isdigit()])
                # Single page
                elif match.isdigit():
                    page_numbers.append(int(match))
        
        return sorted(list(set(page_numbers)))  # Remove duplicates and sort
    
    def verify_citation(self, citation: Dict, pdf_text: str, page_texts: Dict[int, str] = None) -> Dict:
        """
        Verify citation accuracy against PDF content
        
        Args:
            citation: Citation dict from extract_citations()
            pdf_text: Full PDF text
            page_texts: Optional dict mapping page numbers to their text
        
        Returns:
            {
                'verified': bool,
                'confidence_score': float (0-1),
                'issues': List[str],
                'verification_status': str
            }
        """
        issues = []
        confidence_score = 1.0
        
        # Check if quote exists in PDF
        if citation['quote']:
            quote_found = citation['quote'].lower() in pdf_text.lower()
            
            if not quote_found:
                # Try fuzzy matching (allow minor differences)
                quote_found = self._fuzzy_match_quote(citation['quote'], pdf_text)
            
            if not quote_found:
                issues.append("Quoted text not found in document")
                confidence_score -= 0.5
        
        # Verify page numbers exist
        if citation['page_numbers'] and page_texts:
            for page_num in citation['page_numbers']:
                if page_num not in page_texts:
                    issues.append(f"Page {page_num} does not exist in document")
                    confidence_score -= 0.2
        
        # Check classification consistency
        if citation['classification'] == 'DIRECT_QUOTE' and not citation['quote']:
            issues.append("Classified as direct quote but no quote provided")
            confidence_score -= 0.3
        
        # Determine verification status
        if confidence_score >= 0.9:
            status = 'VERIFIED'
        elif confidence_score >= 0.7:
            status = 'LIKELY_ACCURATE'
        elif confidence_score >= 0.5:
            status = 'NEEDS_REVIEW'
        else:
            status = 'QUESTIONABLE'
        
        return {
            'verified': confidence_score >= 0.7,
            'confidence_score': max(0.0, confidence_score),
            'issues': issues,
            'verification_status': status
        }
    
    def _fuzzy_match_quote(self, quote: str, text: str, threshold: float = 0.85) -> bool:
        """Check if quote approximately matches text (allows minor differences)"""
        from difflib import SequenceMatcher
        
        quote_lower = quote.lower()
        text_lower = text.lower()
        
        # Try to find the quote in chunks of similar length
        quote_len = len(quote)
        text_words = text_lower.split()
        quote_words = quote_lower.split()
        
        # Sliding window approach
        for i in range(len(text_words) - len(quote_words) + 1):
            window = ' '.join(text_words[i:i + len(quote_words)])
            similarity = SequenceMatcher(None, quote_lower, window).ratio()
            
            if similarity >= threshold:
                return True
        
        return False
    
    def format_citation_display(self, citation: Dict, verification: Dict = None) -> str:
        """
        Format citation for display in UI
        
        Returns formatted markdown string
        """
        # Confidence badge
        confidence_badges = {
            'High': '🟢',
            'Medium': '🟡',
            'Low': '🔴',
            'Unknown': '⚪'
        }
        
        badge = confidence_badges.get(citation['confidence'], '⚪')
        
        # Verification status
        if verification:
            status_icons = {
                'VERIFIED': '✅',
                'LIKELY_ACCURATE': '✓',
                'NEEDS_REVIEW': '⚠️',
                'QUESTIONABLE': '❌'
            }
            status_icon = status_icons.get(verification['verification_status'], '')
        else:
            status_icon = ''
        
        # Build display
        display = f"""
{citation['answer']}

---

**📍 Source:** {citation['source']}

**{badge} Confidence:** {citation['confidence']} {status_icon}

**📋 Classification:** {citation['classification'].replace('_', ' ').title()}
"""
        
        if citation['quote']:
            quote_text = citation['quote']
            display += f'\n**📝 Quote:** "{quote_text}"'
        
        if verification and verification['issues']:
            display += f"\n\n**⚠️ Verification Issues:**\n"
            for issue in verification['issues']:
                display += f"- {issue}\n"
        
        return display.strip()
    
    def get_confidence_score(self, citation: Dict) -> float:
        """
        Calculate numerical confidence score (0-1)
        """
        # Base score from confidence level
        confidence_scores = {
            'High': 0.9,
            'Medium': 0.7,
            'Low': 0.4,
            'Unknown': 0.3
        }
        
        score = confidence_scores.get(citation['confidence'], 0.3)
        
        # Adjust based on classification
        if citation['classification'] == 'DIRECT_QUOTE':
            score += 0.1
        elif citation['classification'] == 'GENERAL_KNOWLEDGE':
            score -= 0.2
        
        # Adjust based on citation completeness
        if citation['page_numbers']:
            score += 0.05
        if citation['quote']:
            score += 0.05
        
        return min(1.0, max(0.0, score))
