"""
Enhanced Chat Manager
Manages conversation flow, context, and intelligent response handling
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import deque
import hashlib


class ConversationContext:
    """Manages conversation context and history"""
    
    def __init__(self, max_history: int = 10, max_tokens: int = 4000):
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.messages = deque(maxlen=max_history)
        self.metadata = {}
        self.topic_tracking = []
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.messages.append(message)
        
        # Track topics
        if role == 'user':
            self._track_topic(content)
    
    def get_context_window(self, include_system: bool = True) -> List[Dict]:
        """Get optimized context window for LLM"""
        messages = list(self.messages)
        
        # Calculate token usage (rough estimate)
        total_tokens = 0
        context_messages = []
        
        # Add messages from most recent backwards
        for msg in reversed(messages):
            msg_tokens = len(msg['content']) // 4  # Rough estimate
            if total_tokens + msg_tokens > self.max_tokens:
                break
            context_messages.insert(0, {
                'role': msg['role'],
                'content': msg['content']
            })
            total_tokens += msg_tokens
        
        return context_messages
    
    def _track_topic(self, content: str):
        """Track conversation topics for context awareness"""
        # Extract key phrases (simple implementation)
        words = content.lower().split()
        if len(words) > 3:
            topic = ' '.join(words[:5])
            self.topic_tracking.append({
                'topic': topic,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 20 topics
            if len(self.topic_tracking) > 20:
                self.topic_tracking = self.topic_tracking[-20:]
    
    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation"""
        if not self.messages:
            return "No conversation yet"
        
        user_messages = [m for m in self.messages if m['role'] == 'user']
        assistant_messages = [m for m in self.messages if m['role'] == 'assistant']
        
        return f"""
Conversation Summary:
- Total messages: {len(self.messages)}
- User questions: {len(user_messages)}
- AI responses: {len(assistant_messages)}
- Topics discussed: {len(self.topic_tracking)}
"""
    
    def clear(self):
        """Clear conversation history"""
        self.messages.clear()
        self.topic_tracking.clear()


class ResponseFormatter:
    """Formats and enhances AI responses"""
    
    @staticmethod
    def format_markdown(text: str) -> str:
        """Enhanced markdown formatting"""
        # Ensure proper spacing around headers
        text = re.sub(r'(#{1,6})\s*(.+)', r'\1 \2\n', text)
        
        # Ensure proper list formatting
        text = re.sub(r'^\s*[-*]\s+', r'- ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', r'1. ', text, flags=re.MULTILINE)
        
        return text
    
    @staticmethod
    def add_citations_inline(text: str, citations: List[str]) -> str:
        """Add inline citations to text"""
        if not citations:
            return text
        
        citation_text = "\n\n---\n**📚 References:**\n"
        for i, citation in enumerate(citations, 1):
            citation_text += f"{i}. {citation}\n"
        
        return text + citation_text
    
    @staticmethod
    def highlight_key_points(text: str) -> str:
        """Highlight important information"""
        # Bold important phrases
        patterns = [
            (r'\b(important|key point|note|warning|critical)\b', r'**\1**'),
            (r'\b(conclusion|summary|result)\b', r'**\1**'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def format_code_blocks(text: str) -> str:
        """Ensure proper code block formatting"""
        # Fix inline code
        text = re.sub(r'`([^`]+)`', r'`\1`', text)
        
        # Ensure code blocks have language specifiers
        text = re.sub(r'```\n', r'```text\n', text)
        
        return text


class ChatManager:
    """Main chat management system"""
    
    def __init__(self):
        self.context = ConversationContext()
        self.formatter = ResponseFormatter()
        self.response_cache = {}
        self.feedback_history = []
        
    def process_user_message(self, message: str, pdf_context: str = None) -> Dict:
        """Process user message and prepare for LLM"""
        # Clean and validate message
        cleaned_message = self._clean_message(message)
        
        # Check cache for similar questions
        cache_key = self._get_cache_key(cleaned_message, pdf_context)
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            cached['from_cache'] = True
            return cached
        
        # Add to context
        self.context.add_message('user', cleaned_message)
        
        # Build enhanced prompt
        enhanced_prompt = self._enhance_prompt(cleaned_message, pdf_context)
        
        return {
            'original_message': message,
            'cleaned_message': cleaned_message,
            'enhanced_prompt': enhanced_prompt,
            'context_window': self.context.get_context_window(),
            'from_cache': False
        }
    
    def process_ai_response(self, response: str, user_message: str, 
                           pdf_context: str = None, metadata: Dict = None) -> Dict:
        """Process and format AI response"""
        # Format response
        formatted_response = self.formatter.format_markdown(response)
        formatted_response = self.formatter.format_code_blocks(formatted_response)
        
        # Add to context
        self.context.add_message('assistant', formatted_response, metadata)
        
        # Cache response
        cache_key = self._get_cache_key(user_message, pdf_context)
        result = {
            'formatted_response': formatted_response,
            'raw_response': response,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        self.response_cache[cache_key] = result
        
        # Limit cache size
        if len(self.response_cache) > 100:
            # Remove oldest entries
            oldest_keys = list(self.response_cache.keys())[:20]
            for key in oldest_keys:
                del self.response_cache[key]
        
        return result
    
    def regenerate_response(self, message_index: int = -1) -> Optional[str]:
        """Regenerate a specific response"""
        if not self.context.messages:
            return None
        
        # Get the message to regenerate
        messages = list(self.context.messages)
        if abs(message_index) > len(messages):
            return None
        
        target_message = messages[message_index]
        if target_message['role'] != 'assistant':
            return None
        
        # Find the corresponding user message
        user_message_index = message_index - 1
        if user_message_index < 0:
            return None
        
        user_message = messages[user_message_index]
        return user_message['content']
    
    def edit_message(self, message_index: int, new_content: str):
        """Edit a message in the conversation"""
        messages = list(self.context.messages)
        if abs(message_index) > len(messages):
            return False
        
        messages[message_index]['content'] = new_content
        messages[message_index]['edited'] = True
        messages[message_index]['edited_at'] = datetime.now().isoformat()
        
        # Update context
        self.context.messages = deque(messages, maxlen=self.context.max_history)
        return True
    
    def add_feedback(self, message_index: int, feedback: str, rating: int = None):
        """Add feedback to a response"""
        self.feedback_history.append({
            'message_index': message_index,
            'feedback': feedback,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_conversation_stats(self) -> Dict:
        """Get conversation statistics"""
        messages = list(self.context.messages)
        
        user_msgs = [m for m in messages if m['role'] == 'user']
        ai_msgs = [m for m in messages if m['role'] == 'assistant']
        
        # Calculate average response length
        avg_user_length = sum(len(m['content']) for m in user_msgs) / len(user_msgs) if user_msgs else 0
        avg_ai_length = sum(len(m['content']) for m in ai_msgs) / len(ai_msgs) if ai_msgs else 0
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_msgs),
            'ai_messages': len(ai_msgs),
            'avg_user_message_length': int(avg_user_length),
            'avg_ai_message_length': int(avg_ai_length),
            'cache_hits': sum(1 for v in self.response_cache.values() if v.get('from_cache')),
            'feedback_count': len(self.feedback_history)
        }
    
    def export_conversation(self, format: str = 'markdown') -> str:
        """Export conversation in various formats"""
        messages = list(self.context.messages)
        
        if format == 'markdown':
            output = "# Conversation Export\n\n"
            output += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            output += "---\n\n"
            
            for msg in messages:
                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                role_name = "You" if msg['role'] == 'user' else "AI Assistant"
                output += f"## {role_icon} {role_name}\n\n"
                output += f"{msg['content']}\n\n"
                output += "---\n\n"
            
            return output
        
        elif format == 'json':
            import json
            return json.dumps({
                'messages': [dict(m) for m in messages],
                'metadata': self.context.metadata,
                'exported_at': datetime.now().isoformat()
            }, indent=2)
        
        else:  # plain text
            output = f"Conversation Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 60 + "\n\n"
            
            for msg in messages:
                role_name = "You" if msg['role'] == 'user' else "AI Assistant"
                output += f"{role_name}:\n{msg['content']}\n\n"
                output += "-" * 60 + "\n\n"
            
            return output
    
    def clear_conversation(self):
        """Clear all conversation data"""
        self.context.clear()
        self.response_cache.clear()
        self.feedback_history.clear()
    
    def _clean_message(self, message: str) -> str:
        """Clean and normalize user message"""
        # Remove extra whitespace
        message = re.sub(r'\s+', ' ', message).strip()
        
        # Remove potentially harmful content
        message = re.sub(r'<script.*?</script>', '', message, flags=re.IGNORECASE | re.DOTALL)
        
        return message
    
    def _enhance_prompt(self, message: str, pdf_context: str = None) -> str:
        """Enhance user prompt with context"""
        # Get conversation history
        recent_topics = self.context.topic_tracking[-3:] if self.context.topic_tracking else []
        
        enhanced = message
        
        # Add context awareness if there are recent topics
        if recent_topics and len(self.context.messages) > 2:
            enhanced = f"[Context: Previously discussed {', '.join([t['topic'] for t in recent_topics])}]\n\n{message}"
        
        return enhanced
    
    def _get_cache_key(self, message: str, context: str = None) -> str:
        """Generate cache key for message"""
        content = message
        if context:
            content += context[:500]  # Use first 500 chars of context
        
        return hashlib.md5(content.encode()).hexdigest()


class StreamingResponseHandler:
    """Handle streaming responses from LLM"""
    
    def __init__(self):
        self.current_response = ""
        self.chunks = []
        
    def add_chunk(self, chunk: str):
        """Add a chunk of streaming response"""
        self.chunks.append(chunk)
        self.current_response += chunk
    
    def get_current_response(self) -> str:
        """Get current accumulated response"""
        return self.current_response
    
    def reset(self):
        """Reset for new response"""
        self.current_response = ""
        self.chunks.clear()
    
    def format_for_display(self) -> str:
        """Format current response for display"""
        # Add typing indicator if incomplete
        if self.current_response and not self.current_response.endswith(('.', '!', '?')):
            return self.current_response + " ▋"
        return self.current_response
