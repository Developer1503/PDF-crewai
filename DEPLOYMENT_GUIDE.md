# 🚀 Deployment Guide - Updated Research UI

## 📋 Quick Fix for Deployed App

Your localhost works but the deployed version shows the old app. Here's how to fix it:

### **Option 1: Quick Update (Recommended)**

1. **Commit and Push Changes**
   ```bash
   git add .
   git commit -m "Update to new research UI - app_v2.py"
   git push origin main
   ```

2. **Update Streamlit Cloud Settings**
   - Go to [https://share.streamlit.io](https://share.streamlit.io)
   - Find your app
   - Click "⚙️ Settings"
   - Under "Main file path", change to: **`app_v2.py`**
   - Click "Save"
   - App will automatically redeploy

3. **Add Config File** (if not already there)
   - In Streamlit Cloud settings, go to "Advanced settings"
   - Add `.streamlit/config.toml` to your repo (already created locally)
   - This ensures the light theme is used

### **Option 2: Using PowerShell Script**

Run the deployment script:
```powershell
.\deploy.ps1
```

Then follow the prompts to:
1. Commit changes
2. Push to GitHub
3. Update Streamlit Cloud

---

## 🔧 Streamlit Cloud Configuration

### **Main File Path**
Set to: **`app_v2.py`**

### **Python Version**
Recommended: **3.9** or higher

### **Secrets** (Required)
Add these in Streamlit Cloud secrets:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
GOOGLE_API_KEY = "your_google_api_key_here"
```

### **Advanced Settings**
The `.streamlit/config.toml` file is already configured with:
- Light theme
- Purple primary color (#6B46C1)
- Proper background colors

---

## 📝 Step-by-Step Deployment

### **Step 1: Prepare Local Changes**

```bash
# Check what files changed
git status

# Add all changes
git add .

# Commit with a message
git commit -m "Update to new research UI with modern design"

# Push to GitHub
git push origin main
```

### **Step 2: Update Streamlit Cloud**

1. **Login to Streamlit Cloud**
   - Go to [https://share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **Find Your App**
   - Click on your PDF-crewai app

3. **Update Settings**
   - Click "⚙️ Settings" (top right)
   - Under "Main file path": Change to **`app_v2.py`**
   - Click "Save"

4. **Verify Secrets**
   - Go to "Secrets" tab
   - Ensure API keys are set:
     ```toml
     GROQ_API_KEY = "your_key"
     GOOGLE_API_KEY = "your_key"
     ```

5. **Reboot App**
   - Click "⋮ More" → "Reboot app"
   - Or it will auto-deploy after saving settings

### **Step 3: Verify Deployment**

1. Wait for deployment (usually 1-2 minutes)
2. Check the app URL
3. Verify:
   - ✅ Light theme is showing
   - ✅ Purple colors are correct
   - ✅ Research UI design is visible
   - ✅ Upload button works
   - ✅ Chat interface is modern

---

## 🐛 Troubleshooting

### **Issue: Still showing old app**

**Solution:**
1. Hard refresh browser: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache
3. Check Streamlit Cloud logs for errors
4. Verify main file path is `app_v2.py`

### **Issue: Dark theme instead of light**

**Solution:**
1. Ensure `.streamlit/config.toml` is in your repo
2. Commit and push the config file:
   ```bash
   git add .streamlit/config.toml
   git commit -m "Add Streamlit config for light theme"
   git push origin main
   ```
3. Reboot app in Streamlit Cloud

### **Issue: Import errors**

**Solution:**
1. Check `requirements.txt` has all dependencies:
   ```
   streamlit>=1.28.0
   litellm>=1.0.0
   python-dotenv>=1.0.0
   crewai>=0.1.0
   ```
2. Check Streamlit Cloud logs for specific missing packages
3. Add missing packages to `requirements.txt`

### **Issue: API keys not working**

**Solution:**
1. Go to Streamlit Cloud → Secrets
2. Verify format:
   ```toml
   GROQ_API_KEY = "gsk_..."
   GOOGLE_API_KEY = "AIza..."
   ```
3. No quotes around the keys in secrets
4. Reboot app after updating secrets

---

## 📦 Files to Commit

Make sure these files are in your GitHub repo:

### **Required:**
- ✅ `app_v2.py` - Main application
- ✅ `requirements.txt` - Dependencies
- ✅ `.streamlit/config.toml` - Theme configuration
- ✅ `config/` - LLM configuration
- ✅ `tools/` - PDF tools
- ✅ `utils/` - Utilities
- ✅ `components/` - UI components

### **Optional but Recommended:**
- ✅ `README.md` - Documentation
- ✅ `CHAT_QUICK_START.md` - Quick start guide
- ✅ `.gitignore` - Git ignore file
- ✅ `packages.txt` - System packages (if needed)

### **DO NOT Commit:**
- ❌ `.env` - Contains API keys (use Streamlit secrets instead)
- ❌ `__pycache__/` - Python cache
- ❌ `*.pyc` - Compiled Python files

---

## 🚀 Quick Deploy Commands

### **Full Deployment**
```bash
# 1. Stage all changes
git add .

# 2. Commit
git commit -m "Deploy new research UI"

# 3. Push to GitHub
git push origin main

# 4. Streamlit Cloud will auto-deploy
# Or manually reboot from dashboard
```

### **Update Only Config**
```bash
git add .streamlit/config.toml
git commit -m "Update theme configuration"
git push origin main
```

### **Update Only App**
```bash
git add app_v2.py
git commit -m "Update main application"
git push origin main
```

---

## 📊 Deployment Checklist

Before deploying, verify:

- [ ] `app_v2.py` is the main file
- [ ] `.streamlit/config.toml` exists
- [ ] `requirements.txt` is up to date
- [ ] All imports work locally
- [ ] API keys are in Streamlit secrets
- [ ] `.env` is in `.gitignore`
- [ ] All changes are committed
- [ ] Pushed to GitHub main branch

---

## 🎯 Expected Result

After deployment, your app should have:

### **Visual:**
- ✅ Light background (#F9FAFB)
- ✅ Purple theme (#6B46C1)
- ✅ Clean sidebar with "Upload Research" button
- ✅ Document fingerprint section
- ✅ Modern chat interface
- ✅ Confidence indicators
- ✅ Page references

### **Functional:**
- ✅ PDF upload works
- ✅ Chat responses work
- ✅ Quick actions work
- ✅ Navigation works
- ✅ API calls succeed

---

## 📞 Need Help?

If deployment still doesn't work:

1. **Check Streamlit Cloud Logs**
   - Go to your app → "Manage app" → "Logs"
   - Look for error messages

2. **Verify GitHub Repo**
   - Check that `app_v2.py` is in the main branch
   - Verify `.streamlit/config.toml` is present

3. **Test Locally First**
   - Run `streamlit run app_v2.py`
   - Ensure it works before deploying

4. **Common Issues**
   - Wrong main file path
   - Missing dependencies
   - API keys not set
   - Config file not committed

---

## 🎉 Success!

Once deployed successfully, you'll have:
- Modern research UI
- Fast, responsive interface
- Professional appearance
- All features working

**Your deployed app will match your localhost!** 🚀

---

**Last Updated**: 2026-02-13  
**Main File**: `app_v2.py`  
**Theme**: Light with Purple accents  
**Status**: Ready to Deploy ✅
