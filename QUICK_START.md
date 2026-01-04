# 🚀 Quick Start Guide - PDF-crewai v2.0

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

### Step 2: Configure API Keys (1 min)

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here
```

**Get API Keys:**
- **Groq**: https://console.groq.com/keys (Free, instant)
- **Google Gemini**: https://makersuite.google.com/app/apikey (Free)

### Step 3: Run the App (1 min)

```bash
streamlit run app_v2.py
```

### Step 4: Upload & Analyze (1 min)

1. Open browser (auto-opens to http://localhost:8501)
2. Upload a PDF
3. Review document fingerprint
4. Ask questions!

---

## 🎯 First-Time User Flow

### **1. Upload Your First PDF**

```
📤 Upload Section
├── Click "Choose a PDF file"
├── Select any PDF (contract, paper, report)
└── Wait 5-10 seconds for analysis
```

**What Happens:**
- ✅ PDF validated (size, quality, text extraction)
- ✅ Document fingerprint generated
- ✅ Metadata extracted (dates, entities, sections)
- ✅ Suggested questions created
- ✅ Document stored locally (compressed)

### **2. Review Document Fingerprint**

You'll see:
```
📄 Document Fingerprint
├── Type: Legal Contract (85% confidence)
├── Length: 12,450 words (~45 pages)
├── Read Time: 62 min
├── Key Dates: 2025-06-15, 2026-01-01
├── Entities: Acme Corp, TechVendor Inc
└── Suggested Questions:
    • What are the payment terms?
    • List all key dates
    • What are termination clauses?
```

### **3. Ask Your First Question**

**Option A: Quick Actions**
- Click "📝 Summarize" for instant summary
- Click "🔍 Key Findings" for main points
- Click "📊 Analyze" for deep analysis

**Option B: Custom Question**
- Type in text box: "What are the payment terms?"
- Press "Send 🚀"

**Option C: Voice Input** (if available)
- Click microphone icon 🎤
- Speak your question
- Click again to stop
- Auto-transcribed and sent

### **4. Review Response with Citations**

Response format:
```
🤖 AI Assistant

**Answer:** The payment terms specify net 30 days...

───────────────────────────────────────
📍 Source: Page 12, Section 5.2
🟢 Confidence: High (Direct Quote)
📋 Classification: Direct Quote
📝 Quote: "Payment shall be made within 30 days..."
```

### **5. Export Your Work**

Sidebar → Export Section:
```
📥 Export
├── Format: [Markdown ▼]
└── [📥 Export Conversation]
```

Choose from:
- **Markdown**: For documentation
- **JSON**: For automation
- **HTML**: For sharing
- **Text**: For simple backup
- **Summary Report**: Comprehensive analysis

---

## 💡 Pro Tips

### **Optimize Token Usage**

1. **Enable Turbo Mode** (Sidebar → ⚡ Turbo Mode)
   - Uses smaller, faster models
   - Saves 50% of quota
   - Slightly less detailed responses

2. **Ask Specific Questions**
   - ❌ Bad: "Tell me about this document"
   - ✅ Good: "What are the payment terms in Section 5?"

3. **Use Quick Actions**
   - Pre-optimized queries
   - Faster responses
   - Better results

### **Manage Storage**

1. **Check Usage** (Sidebar → 💾 Storage)
   ```
   Documents: 3
   Storage Used: 15.2%
   ```

2. **Cleanup Old Data**
   - Auto-deletes after 30 days
   - Manual cleanup: Click "🧹 Cleanup Old Data"

3. **Export Before Deleting**
   - Save important conversations
   - Download as Markdown/JSON

### **Handle Errors Gracefully**

When you see:
```
🟡 High Traffic Detected
⏱️ Estimated wait: 30 seconds
```

**Do:**
- ✅ Wait for automatic retry
- ✅ Switch providers (auto-handled)
- ✅ Ask simpler question

**Don't:**
- ❌ Refresh page (loses progress)
- ❌ Spam retry button
- ❌ Close browser

### **Use Legal-Grade Citations**

For important documents:
1. Enable "⚖️ Legal-Grade Citations" (Sidebar)
2. Responses will be slower but more accurate
3. Citations verified against source
4. Hallucinations flagged

---

## 🎓 Example Workflows

### **Workflow 1: Contract Review**

```bash
1. Upload: contract.pdf
2. Review fingerprint
3. Quick Action: "📝 Summarize"
4. Ask: "What are the termination clauses?"
5. Ask: "List all key dates and deadlines"
6. Ask: "What are the payment terms?"
7. Export: Summary Report (Markdown)
```

**Time:** 5-7 minutes  
**Tokens Used:** ~3,000

### **Workflow 2: Research Paper Analysis**

```bash
1. Upload: research_paper.pdf
2. Review fingerprint
3. Ask: "What is the methodology?"
4. Ask: "What are the key findings?"
5. Ask: "What are the limitations?"
6. Ask: "How does this compare to [other paper]?"
7. Export: Markdown (for notes)
```

**Time:** 8-10 minutes  
**Tokens Used:** ~4,500

### **Workflow 3: Multi-Document Comparison**

```bash
1. Upload: contract_v1.pdf
2. Analyze and export
3. Upload: contract_v2.pdf
4. Ask: "What changed between v1 and v2?"
5. Ask: "Are there any conflicting clauses?"
6. Export: Summary Report
```

**Time:** 10-12 minutes  
**Tokens Used:** ~6,000

---

## 🔧 Troubleshooting

### **App Won't Start**

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Clear cache
streamlit cache clear
```

### **PDF Upload Fails**

**Error:** "Failed to read PDF"

**Solutions:**
1. Check file is valid PDF (not corrupted)
2. Try smaller file (<20MB recommended)
3. If scanned PDF, text extraction limited
4. Use different PDF reader to re-save

### **Voice Input Not Working**

**Error:** "Could not understand audio"

**Solutions:**
1. Speak more clearly
2. Reduce background noise
3. Check microphone permissions
4. Use text input instead

### **Rate Limit Errors**

**Error:** "🟡 High Traffic Detected"

**Solutions:**
1. Wait 30-60 seconds (auto-retries)
2. Enable Turbo Mode
3. Ask shorter questions
4. Switch providers manually

### **Storage Full**

**Warning:** "⚠️ Storage is running low"

**Solutions:**
1. Export important conversations
2. Click "🧹 Cleanup Old Data"
3. Delete unused documents
4. Reduce document retention (modify TTL)

---

## 📊 Performance Benchmarks

### **Response Times** (Average)

| Question Type | Turbo Mode | Standard Mode |
|---------------|------------|---------------|
| Yes/No | 2s | 3s |
| Summary | 5s | 8s |
| Analysis | 10s | 15s |
| Comparison | 15s | 25s |

### **Token Usage** (Average)

| Action | Tokens | Cost (Free Tier) |
|--------|--------|------------------|
| Simple Q&A | 500 | ✅ Free |
| Summary | 1,500 | ✅ Free |
| Deep Analysis | 3,000 | ✅ Free |
| Multi-doc Compare | 5,000 | ✅ Free |

**Daily Limits:**
- Groq: ~50,000 tokens/day
- Gemini: ~1,000,000 tokens/day

---

## 🎯 Next Steps

### **After First Use**

1. ✅ Explore all Quick Actions
2. ✅ Try voice input
3. ✅ Export a conversation
4. ✅ Enable Legal-Grade Citations
5. ✅ Upload multiple documents

### **Advanced Features**

1. **Multi-Document Workspace**
   - Upload 5+ documents
   - Compare across documents
   - Build document network

2. **Custom Workflows**
   - Create saved question templates
   - Automate common analyses
   - Build personal knowledge base

3. **Integration**
   - Export to Notion/Obsidian
   - Integrate with automation tools
   - Build custom scripts

---

## 📚 Learn More

- [Full Documentation](README.md)
- [Rate Limit Guide](RATE_LIMIT_GUIDE.md)
- [Voice Input Guide](VOICE_INPUT_GUIDE.md)
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)

---

## 🆘 Get Help

**Issues?**
- Check [Troubleshooting](#troubleshooting) section
- Search [GitHub Issues](https://github.com/yourusername/PDF-crewai/issues)
- Ask in [Discussions](https://github.com/yourusername/PDF-crewai/discussions)

**Feature Requests?**
- Open an issue with `[Feature Request]` tag
- Describe use case and expected behavior
- Include examples if possible

---

**Happy Analyzing! 🚀**

*Last Updated: January 4, 2026*
