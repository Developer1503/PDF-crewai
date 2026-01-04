"""
Query Optimizer
Validates and optimizes queries before sending to LLM to save tokens
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


class QueryOptimizer:
    """
    Optimizes user queries to reduce token usage and improve response quality
    """
    
    VAGUE_PATTERNS = [
        'tell me about', 'explain this', 'what is this', 'describe',
        'give me information', 'what about', 'talk about'
    ]
    
    BROAD_PATTERNS = [
        'everything', 'all information', 'complete', 'entire', 'whole',
        'every', 'all details', 'comprehensive'
    ]
    
    OPTIMAL_INDICATORS = [
        'page', 'section', 'paragraph', 'clause', 'chapter',
        'specific', 'particular', 'exact', 'line'
    ]
    
    def __init__(self):
        self.query_history = []
    
    def score_question_quality(self, question: str) -> Dict:
        """
        Score question quality and provide suggestions
        
        Returns:
            {
                'score': float (0-1),
                'quality': str ('optimal', 'good', 'vague', 'too_broad'),
                'suggestions': List[str],
                'issues': List[str]
            }
        """
        question_lower = question.lower()
        score = 1.0
        issues = []
        suggestions = []
        
        # Check for vague patterns
        if any(pattern in question_lower for pattern in self.VAGUE_PATTERNS):
            score -= 0.3
            issues.append('Question is too vague')
            suggestions.append('Be more specific about what you want to know')
        
        # Check for overly broad patterns
        if any(pattern in question_lower for pattern in self.BROAD_PATTERNS):
            score -= 0.4
            issues.append('Question is too broad')
            suggestions.append('Focus on a specific aspect or section')
        
        # Check for optimal indicators
        has_optimal = any(indicator in question_lower for indicator in self.OPTIMAL_INDICATORS)
        if has_optimal:
            score += 0.2
        
        # Check question length
        word_count = len(question.split())
        if word_count < 3:
            score -= 0.2
            issues.append('Question is too short')
            suggestions.append('Add more context to your question')
        elif word_count > 50:
            score -= 0.1
            issues.append('Question is very long')
            suggestions.append('Try breaking into multiple shorter questions')
        
        # Determine quality level
        score = max(0.0, min(1.0, score))
        
        if score >= 0.8:
            quality = 'optimal'
        elif score >= 0.6:
            quality = 'good'
        elif score >= 0.4:
            quality = 'vague'
        else:
            quality = 'too_broad'
        
        return {
            'score': score,
            'quality': quality,
            'suggestions': suggestions,
            'issues': issues
        }
    
    def find_duplicate_question(self, question: str, threshold: float = 0.85) -> Optional[Dict]:
        """
        Check if similar question was asked before
        
        Returns previous Q&A if found, None otherwise
        """
        question_lower = question.lower().strip()
        
        for prev_qa in self.query_history:
            prev_question = prev_qa['question'].lower().strip()
            
            # Calculate similarity
            similarity = SequenceMatcher(None, question_lower, prev_question).ratio()
            
            if similarity >= threshold:
                return {
                    'previous_question': prev_qa['question'],
                    'previous_answer': prev_qa.get('answer', ''),
                    'similarity': similarity,
                    'timestamp': prev_qa.get('timestamp', '')
                }
        
        return None
    
    def add_to_history(self, question: str, answer: str = ''):
        """Add question to history for duplicate detection"""
        from datetime import datetime
        
        self.query_history.append({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 questions
        if len(self.query_history) > 50:
            self.query_history = self.query_history[-50:]
    
    def preprocess_question(self, question: str) -> str:
        """
        Clean and optimize question text
        
        - Expand abbreviations
        - Remove filler words
        - Fix common typos
        """
        # Expand common abbreviations
        abbreviations = {
            "what's": "what is",
            "that's": "that is",
            "it's": "it is",
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
        }
        
        for abbr, expansion in abbreviations.items():
            question = re.sub(r'\b' + abbr + r'\b', expansion, question, flags=re.IGNORECASE)
        
        # Remove filler words
        fillers = ['um', 'uh', 'like', 'you know', 'i mean', 'basically', 'actually']
        for filler in fillers:
            question = re.sub(r'\b' + filler + r'\b', '', question, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        question = re.sub(r'\s+', ' ', question).strip()
        
        return question
    
    def estimate_token_cost(self, question: str, context: str) -> Dict:
        """
        Estimate token cost for the query
        
        Returns:
            {
                'question_tokens': int,
                'context_tokens': int,
                'total_input_tokens': int,
                'estimated_output_tokens': int,
                'total_estimated_tokens': int
            }
        """
        # Rough estimation: 1 token ≈ 4 characters
        question_tokens = len(question) // 4
        context_tokens = len(context) // 4
        
        # Estimate output based on question type
        if any(word in question.lower() for word in ['summarize', 'summary', 'overview']):
            estimated_output = 200
        elif any(word in question.lower() for word in ['yes', 'no', 'is', 'does', 'can']):
            estimated_output = 50
        elif any(word in question.lower() for word in ['list', 'enumerate', 'what are']):
            estimated_output = 150
        else:
            estimated_output = 300
        
        return {
            'question_tokens': question_tokens,
            'context_tokens': context_tokens,
            'total_input_tokens': question_tokens + context_tokens,
            'estimated_output_tokens': estimated_output,
            'total_estimated_tokens': question_tokens + context_tokens + estimated_output
        }
    
    def suggest_better_questions(self, question: str, document_type: str = 'general') -> List[str]:
        """
        Suggest better formulations of the question
        """
        suggestions = []
        question_lower = question.lower()
        
        # Generic improvements
        if 'tell me about' in question_lower:
            topic = question_lower.replace('tell me about', '').strip()
            suggestions.append(f"What are the key points about {topic}?")
            suggestions.append(f"Summarize the information about {topic}")
        
        if 'explain this' in question_lower or 'what is this' in question_lower:
            suggestions.append("What is the main topic of this document?")
            suggestions.append("Summarize this document in 3 sentences")
        
        # Document-type specific suggestions
        if document_type == 'legal_contract':
            if not any(word in question_lower for word in ['page', 'section', 'clause']):
                suggestions.append("Try: 'What are the payment terms in Section X?'")
                suggestions.append("Try: 'List the termination clauses'")
        
        elif document_type == 'research_paper':
            if 'methodology' not in question_lower and 'findings' not in question_lower:
                suggestions.append("Try: 'What methodology was used?'")
                suggestions.append("Try: 'What are the key findings?'")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def optimize_context(self, full_context: str, question: str, max_tokens: int = 3000) -> str:
        """
        Reduce context size by extracting only relevant parts
        
        This is a simple keyword-based approach
        For production, use semantic similarity with embeddings
        """
        # Extract keywords from question
        keywords = self._extract_keywords(question)
        
        # Split context into paragraphs
        paragraphs = full_context.split('\n\n')
        
        # Score each paragraph by keyword relevance
        scored_paragraphs = []
        for para in paragraphs:
            if not para.strip():
                continue
            
            score = sum(1 for keyword in keywords if keyword.lower() in para.lower())
            scored_paragraphs.append((score, para))
        
        # Sort by relevance
        scored_paragraphs.sort(reverse=True, key=lambda x: x[0])
        
        # Build optimized context within token limit
        optimized = []
        current_tokens = 0
        
        for score, para in scored_paragraphs:
            para_tokens = len(para) // 4
            if current_tokens + para_tokens > max_tokens:
                break
            optimized.append(para)
            current_tokens += para_tokens
        
        return '\n\n'.join(optimized)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords
