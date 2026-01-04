"""
Intelligent Error Handler
Transforms technical errors into user-friendly, actionable messages
"""

import re
from typing import Tuple, Optional, Dict
from datetime import datetime


class ErrorHandler:
    """
    Classifies errors and provides user-friendly messages with recovery actions
    """
    
    ERROR_TYPES = {
        'RATE_LIMIT': {
            'patterns': ['429', 'quota', 'rate limit', 'resource_exhausted', 'too many requests'],
            'severity': 'warning',
            'icon': '🟡'
        },
        'TIMEOUT': {
            'patterns': ['timeout', 'timed out', 'deadline exceeded'],
            'severity': 'warning',
            'icon': '🟠'
        },
        'INVALID_RESPONSE': {
            'patterns': ['malformed', 'invalid json', 'parse error', 'unexpected response'],
            'severity': 'error',
            'icon': '🔴'
        },
        'AUTH_FAILURE': {
            'patterns': ['401', '403', 'unauthorized', 'forbidden', 'invalid api key'],
            'severity': 'error',
            'icon': '🔴'
        },
        'NETWORK': {
            'patterns': ['connection', 'network', 'unreachable', 'dns'],
            'severity': 'warning',
            'icon': '🟠'
        },
        'CONTEXT_LENGTH': {
            'patterns': ['context length', 'token limit', 'too long', 'maximum context'],
            'severity': 'warning',
            'icon': '🟡'
        }
    }
    
    def __init__(self):
        self.error_log = []
    
    def classify_error(self, error: Exception) -> str:
        """Classify error type based on message content"""
        error_str = str(error).lower()
        
        for error_type, config in self.ERROR_TYPES.items():
            for pattern in config['patterns']:
                if pattern in error_str:
                    return error_type
        
        return 'UNKNOWN'
    
    def extract_retry_delay(self, error: Exception) -> Optional[int]:
        """Extract retry delay from error message (in seconds)"""
        error_str = str(error)
        
        # Look for patterns like "retry after 60 seconds" or "wait 1 minute"
        patterns = [
            r'retry after (\d+) seconds?',
            r'wait (\d+) seconds?',
            r'try again in (\d+) seconds?',
            r'retry in (\d+)s',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Look for minute patterns
        minute_patterns = [
            r'retry after (\d+) minutes?',
            r'wait (\d+) minutes?',
        ]
        
        for pattern in minute_patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                return int(match.group(1)) * 60
        
        return None
    
    def get_user_message(self, error: Exception, context: Dict = None) -> Dict:
        """
        Convert technical error to user-friendly message with actions
        
        Returns:
            {
                'title': str,
                'message': str,
                'icon': str,
                'severity': str,
                'actions': List[str],
                'retry_delay': Optional[int],
                'technical_details': str (for debugging)
            }
        """
        error_type = self.classify_error(error)
        retry_delay = self.extract_retry_delay(error)
        context = context or {}
        
        # Log error
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': str(error),
            'context': context
        })
        
        # Generate user-friendly message
        if error_type == 'RATE_LIMIT':
            return self._handle_rate_limit(error, retry_delay, context)
        elif error_type == 'TIMEOUT':
            return self._handle_timeout(error, context)
        elif error_type == 'INVALID_RESPONSE':
            return self._handle_invalid_response(error, context)
        elif error_type == 'AUTH_FAILURE':
            return self._handle_auth_failure(error, context)
        elif error_type == 'NETWORK':
            return self._handle_network(error, context)
        elif error_type == 'CONTEXT_LENGTH':
            return self._handle_context_length(error, context)
        else:
            return self._handle_unknown(error, context)
    
    def _handle_rate_limit(self, error: Exception, retry_delay: Optional[int], context: Dict) -> Dict:
        """Handle rate limit errors"""
        provider = context.get('provider', 'AI service')
        
        if retry_delay:
            wait_msg = f"{retry_delay} seconds"
        else:
            wait_msg = "a moment"
        
        return {
            'title': '🟡 High Traffic Detected',
            'message': f"""Our free {provider} service is popular right now!

⏱️ Estimated wait: {wait_msg}
📊 The system will automatically switch to a backup provider.

**Meanwhile, you can:**
• View your document
• Ask a simpler question
• Wait and retry automatically""",
            'icon': '🟡',
            'severity': 'warning',
            'actions': ['switch_provider', 'simplify_query', 'wait_retry'],
            'retry_delay': retry_delay or 30,
            'technical_details': str(error)
        }
    
    def _handle_timeout(self, error: Exception, context: Dict) -> Dict:
        """Handle timeout errors"""
        return {
            'title': '🟠 Request Taking Longer Than Expected',
            'message': """The AI is taking longer to respond than usual.

**This might be because:**
• Network connection is slow
• Large document being processed
• High server load

**What you can do:**
• Wait a bit longer (extending timeout)
• Try a shorter question
• Check your internet connection""",
            'icon': '🟠',
            'severity': 'warning',
            'actions': ['extend_timeout', 'simplify_query', 'check_network'],
            'retry_delay': 10,
            'technical_details': str(error)
        }
    
    def _handle_invalid_response(self, error: Exception, context: Dict) -> Dict:
        """Handle malformed response errors"""
        return {
            'title': '🔴 Unexpected Response Format',
            'message': """The AI returned data in an unexpected format.

**We're attempting to:**
• Parse the response differently
• Retry with adjusted settings
• Switch to a backup provider

**You can:**
• Try asking your question again
• Rephrase your question
• Report this issue if it persists""",
            'icon': '🔴',
            'severity': 'error',
            'actions': ['retry', 'rephrase', 'report'],
            'retry_delay': 5,
            'technical_details': str(error)
        }
    
    def _handle_auth_failure(self, error: Exception, context: Dict) -> Dict:
        """Handle authentication errors"""
        provider = context.get('provider', 'API')
        
        return {
            'title': '🔴 Authentication Issue',
            'message': f"""There's a problem with the {provider} API key.

**Possible causes:**
• API key is invalid or expired
• API key doesn't have required permissions
• Service is temporarily unavailable

**What to do:**
• Check your .env file for correct API keys
• Verify API key is active in provider dashboard
• Try switching to another provider""",
            'icon': '🔴',
            'severity': 'error',
            'actions': ['check_api_key', 'switch_provider', 'view_docs'],
            'retry_delay': None,
            'technical_details': str(error)
        }
    
    def _handle_network(self, error: Exception, context: Dict) -> Dict:
        """Handle network errors"""
        return {
            'title': '🟠 Network Connection Issue',
            'message': """Unable to reach the AI service.

**Please check:**
• Your internet connection is active
• Firewall isn't blocking the request
• VPN isn't interfering

**We'll automatically:**
• Retry the request
• Switch to backup provider if available""",
            'icon': '🟠',
            'severity': 'warning',
            'actions': ['check_network', 'retry', 'switch_provider'],
            'retry_delay': 15,
            'technical_details': str(error)
        }
    
    def _handle_context_length(self, error: Exception, context: Dict) -> Dict:
        """Handle context length errors"""
        return {
            'title': '🟡 Document Too Large for Single Query',
            'message': """Your question requires too much context for the AI model.

**We can help by:**
• Breaking your question into smaller parts
• Focusing on specific sections of the document
• Using a model with larger context window

**Try:**
• Ask about a specific page or section
• Simplify your question
• Enable "Smart Chunking" mode""",
            'icon': '🟡',
            'severity': 'warning',
            'actions': ['chunk_query', 'specify_section', 'use_larger_model'],
            'retry_delay': None,
            'technical_details': str(error)
        }
    
    def _handle_unknown(self, error: Exception, context: Dict) -> Dict:
        """Handle unknown errors"""
        return {
            'title': '🔴 Unexpected Error',
            'message': """Something unexpected happened.

**We're working on it:**
• Logging the error for investigation
• Attempting automatic recovery
• Preserving your work

**You can:**
• Try your action again
• Refresh the page if problem persists
• Contact support with error details""",
            'icon': '🔴',
            'severity': 'error',
            'actions': ['retry', 'refresh', 'report'],
            'retry_delay': 5,
            'technical_details': str(error)
        }
    
    def get_error_stats(self) -> Dict:
        """Get error statistics for analytics"""
        if not self.error_log:
            return {'total': 0, 'by_type': {}}
        
        by_type = {}
        for entry in self.error_log:
            error_type = entry['type']
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            'total': len(self.error_log),
            'by_type': by_type,
            'recent': self.error_log[-10:]  # Last 10 errors
        }
    
    def clear_error_log(self):
        """Clear error log"""
        self.error_log = []
