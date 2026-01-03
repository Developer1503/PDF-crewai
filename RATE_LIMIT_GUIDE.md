# Rate Limit Handling Guide

## Overview
This document explains the comprehensive rate limit handling system implemented in the PDF Research Crew application.

## Problem
You encountered a **429 RESOURCE_EXHAUSTED** error from the Gemini API, indicating:
- Exceeded input token count per minute
- Exceeded requests per minute
- Exceeded requests per day (free tier limits)

## Solution Implemented

### 1. **Smart Provider Fallback**
The application now automatically switches between providers when rate limits are hit:
- **Primary**: Groq (default) - More generous free tier
- **Fallback**: Gemini - Backup when Groq is exhausted

### 2. **Exponential Backoff Retry**
When rate limits are encountered:
- Automatically retries with increasing wait times (5s, 10s, 20s)
- Extracts retry delay from error messages
- Maximum 3 retries per provider before switching

### 3. **Smaller Models by Default**
To conserve tokens and avoid hitting limits:
- **Groq**: `llama-3.1-8b-instant` (Turbo Mode ON)
- **Gemini**: `gemini-1.5-flash` (more stable than experimental)
- Toggle "Turbo Mode" in the UI to switch between model sizes

### 4. **Enhanced Error Handling**
- Detects rate limit errors automatically
- Provides clear, actionable guidance to users
- Shows detailed error information in expandable sections
- Offers "Wait 60s & Retry" button for convenience

## Key Changes Made

### `config/llm.py`
- Added `is_rate_limit_error()` - Detects quota/rate limit errors
- Added `extract_retry_delay()` - Parses retry time from error messages
- Updated `get_llm()` - Defaults to Groq with smaller models
- Enhanced `get_llm_with_fallback()` - Exponential backoff retry logic
- Added `get_llm_with_smart_fallback()` - Immediate provider switching

### `app.py`
- Changed default provider from Gemini to Groq
- Integrated smart fallback in analysis pipeline
- Updated chat interface to use fallback mechanism
- Enhanced error messages with specific guidance
- Added "Wait & Retry" functionality

## How to Use

### Immediate Actions
1. **Wait 60 seconds** - Your Gemini quota will reset shortly
2. **Use Groq** - The app now defaults to Groq to avoid Gemini limits
3. **Enable Turbo Mode** - Uses smaller models (already ON by default)

### If You Still Hit Limits
1. Click "⏰ Wait 60s & Retry" button
2. Try switching providers in the sidebar
3. Wait a few minutes between analyses
4. Consider upgrading to paid API tiers for higher limits

### Monitoring Quota
- **Gemini**: https://ai.dev/usage?tab=rate-limit
- **Groq**: https://console.groq.com/usage

## API Quota Limits

### Gemini Free Tier (gemini-1.5-flash)
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

### Groq Free Tier
- Varies by model
- Generally more generous than Gemini for burst usage
- Check: https://console.groq.com/docs/rate-limits

## Best Practices

1. **Use Turbo Mode** - Enabled by default, uses smaller models
2. **Batch Processing** - Analyze multiple PDFs with delays between them
3. **Monitor Usage** - Check quota dashboards regularly
4. **Upgrade When Needed** - Consider paid tiers for production use
5. **Choose Quick Analysis** - Use "Quick" depth instead of "Deep" to save tokens

## Troubleshooting

### "All providers exhausted"
- Both Gemini and Groq have hit rate limits
- Wait 5-10 minutes for limits to reset
- Check your API keys in `.env` file

### "Failed to initialize LLM"
- API key might be invalid or missing
- Check `.env` file has both keys:
  ```
  GROQ_API_KEY=your_key_here
  GOOGLE_API_KEY=your_key_here
  ```

### Chat quota exceeded
- Chat uses the same quota as analysis
- Wait a moment before sending more messages
- Reduce message frequency

## Technical Details

### Rate Limit Detection
The system detects rate limits by checking for these indicators:
- HTTP 429 status code
- "RESOURCE_EXHAUSTED" status
- "quota" in error message
- "rate limit" in error message

### Retry Strategy
```
Attempt 1: Wait 5 seconds
Attempt 2: Wait 10 seconds
Attempt 3: Wait 20 seconds
If all fail: Switch to next provider
```

### Provider Priority
```
User selects Groq → Try Groq (3 attempts) → Fallback to Gemini (3 attempts)
User selects Gemini → Try Gemini (3 attempts) → Fallback to Groq (3 attempts)
```

## Next Steps

Your application should now work reliably with automatic rate limit handling. The changes ensure:
- ✅ Automatic provider switching
- ✅ Intelligent retry with backoff
- ✅ Clear error messages
- ✅ Token conservation
- ✅ Better user experience

**Try running your analysis again!** The app will now automatically handle rate limits and switch providers as needed.
