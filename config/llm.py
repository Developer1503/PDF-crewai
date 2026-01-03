import os
import time
import logging
from crewai import LLM
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit errors"""
    pass

def is_rate_limit_error(error_message: str) -> bool:
    """Check if error is a rate limit error"""
    rate_limit_indicators = [
        "429",
        "RESOURCE_EXHAUSTED",
        "quota",
        "rate limit",
        "rate_limit",
        "too many requests"
    ]
    error_str = str(error_message).lower()
    return any(indicator.lower() in error_str for indicator in rate_limit_indicators)

def extract_retry_delay(error_message: str) -> float:
    """Extract retry delay from error message, default to 60 seconds"""
    import re
    # Look for patterns like "retry in 57.910040681s" or "57s"
    match = re.search(r'retry.*?(\d+\.?\d*)\s*s', str(error_message), re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 60.0  # Default to 60 seconds

def get_llm(provider="groq", use_smaller_model=True):
    """
    Returns an LLM instance based on provider.
    Supported: 'groq', 'gemini'
    Uses CrewAI's native LLM class which wraps LiteLLM.
    
    Args:
        provider: 'groq' or 'gemini' (default: 'groq' to avoid Gemini quota issues)
        use_smaller_model: If True, use smaller/faster models to save tokens (default: True)
    """

    if provider == "gemini":
        # Use Gemini - but be aware of free tier limits
        # Switching to a more stable model
        model = "gemini/gemini-1.5-flash"  # More stable than experimental
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        return LLM(
            model=model,
            temperature=0.3,
            api_key=api_key
        )

    if provider == "groq":
        # Use smaller model by default to conserve tokens
        if use_smaller_model:
            model = "groq/llama-3.1-8b-instant"  # Much smaller, faster, uses fewer tokens
        else:
            model = "groq/llama-3.3-70b-versatile"
        
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        return LLM(
            model=model,
            temperature=0.3,
            api_key=api_key
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")


def get_llm_with_fallback(primary_provider="groq", use_smaller_model=True, max_retries=3) -> Tuple[LLM, str]:
    """
    Try primary provider with exponential backoff, fall back to secondary if rate limited.
    
    Args:
        primary_provider: Primary provider to try first (default: 'groq')
        use_smaller_model: Use smaller models to conserve tokens (default: True)
        max_retries: Maximum number of retries per provider (default: 3)
    
    Returns:
        Tuple of (llm_instance, provider_used)
    
    Raises:
        Exception: If all providers fail
    """
    # Prioritize Groq first to avoid Gemini quota issues
    providers = ["groq", "gemini"] if primary_provider == "groq" else ["gemini", "groq"]
    
    last_error = None
    
    for provider in providers:
        logger.info(f"Attempting to use provider: {provider}")
        
        # Try with exponential backoff
        for attempt in range(max_retries):
            try:
                llm = get_llm(provider=provider, use_smaller_model=use_smaller_model)
                logger.info(f"Successfully initialized LLM with provider: {provider}")
                return llm, provider
                
            except Exception as e:
                error_msg = str(e)
                last_error = e
                
                # Check if it's a rate limit error
                if is_rate_limit_error(error_msg):
                    retry_delay = extract_retry_delay(error_msg)
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2^attempt * base_delay
                        wait_time = min(retry_delay, 2 ** attempt * 5)
                        logger.warning(
                            f"Rate limit hit for {provider} (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.1f}s before retry..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries reached for {provider}. Trying next provider...")
                        break
                else:
                    # Non-rate-limit error, try next provider immediately
                    logger.error(f"Error with {provider}: {error_msg}")
                    break
    
    # If all providers fail, raise the last error with helpful message
    error_message = (
        f"All LLM providers failed. Last error: {last_error}\n\n"
        "Possible solutions:\n"
        "1. Wait a few minutes for rate limits to reset\n"
        "2. Check your API keys in .env file\n"
        "3. Verify you have available quota for both Gemini and Groq\n"
        "4. Consider upgrading to a paid tier for higher limits"
    )
    raise Exception(error_message)


def get_llm_with_smart_fallback(primary_provider="groq", use_smaller_model=True) -> Tuple[LLM, str]:
    """
    Intelligent fallback with immediate switch on quota errors.
    
    This function tries the primary provider once, and if it hits a quota/rate limit,
    immediately switches to the fallback provider without retrying.
    
    Args:
        primary_provider: Primary provider to try first (default: 'groq')
        use_smaller_model: Use smaller models (default: True)
    
    Returns:
        Tuple of (llm_instance, provider_used)
    """
    providers = ["groq", "gemini"] if primary_provider == "groq" else ["gemini", "groq"]
    
    for provider in providers:
        try:
            llm = get_llm(provider=provider, use_smaller_model=use_smaller_model)
            logger.info(f"Using provider: {provider}")
            return llm, provider
        except Exception as e:
            if is_rate_limit_error(str(e)):
                logger.warning(f"Rate limit detected for {provider}, switching to fallback...")
                continue
            else:
                logger.error(f"Error with {provider}: {e}")
                continue
    
    raise Exception("All providers exhausted. Please check your API keys and quotas.")
