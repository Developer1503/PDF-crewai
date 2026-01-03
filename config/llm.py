import os
from crewai import LLM

def get_llm(provider="gemini", use_smaller_model=False):
    """
    Returns an LLM instance based on provider.
    Supported: 'groq', 'gemini'
    Uses CrewAI's native LLM class which wraps LiteLLM.
    
    Args:
        provider: 'groq' or 'gemini'
        use_smaller_model: If True, use smaller/faster models to save tokens
    """

    if provider == "gemini":
        # Use Gemini - more generous rate limits
        model = "gemini/gemini-2.0-flash-exp"
        return LLM(
            model=model,
            temperature=0.3,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

    if provider == "groq":
        # Use smaller model if requested (saves tokens)
        if use_smaller_model:
            model = "groq/llama-3.1-8b-instant"  # Much smaller, faster, uses fewer tokens
        else:
            model = "groq/llama-3.3-70b-versatile"
        
        return LLM(
            model=model,
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )

    raise ValueError("Unsupported LLM provider")


def get_llm_with_fallback(primary_provider="gemini", use_smaller_model=False):
    """
    Try primary provider, fall back to secondary if rate limited.
    Returns tuple: (llm, provider_used)
    """
    providers = ["gemini", "groq"] if primary_provider == "gemini" else ["groq", "gemini"]
    
    for provider in providers:
        try:
            llm = get_llm(provider=provider, use_smaller_model=use_smaller_model)
            return llm, provider
        except Exception as e:
            continue
    
    # Last resort - try any provider with smaller model
    return get_llm(provider="gemini", use_smaller_model=True), "gemini"
