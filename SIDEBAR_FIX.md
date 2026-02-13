# 🔧 Sidebar Not Showing - Quick Fix

## Problem
The sidebar with "Upload Research" button is not visible on the deployed app.

## Solution 1: Click the Hamburger Menu (Quickest)

**On your deployed app:**
1. Look at the **top-left corner** of the screen
2. You should see a **hamburger menu icon (☰)** or **arrow (>)**
3. **Click it** to expand the sidebar
4. The sidebar will appear with the purple "Upload Research" button

## Solution 2: Update and Redeploy

If the hamburger menu doesn't work, redeploy with updated config:

### Step 1: Commit Changes
```bash
git add .streamlit/config.toml
git commit -m "Fix sidebar visibility"
git push origin main
```

### Step 2: Wait for Auto-Deploy
- Streamlit Cloud will automatically redeploy
- Wait 2-3 minutes
- Refresh your browser

### Step 3: Force Sidebar Open
- The updated config forces sidebar to be expanded
- Sidebar should now be visible by default

## Solution 3: Browser Settings

If sidebar still doesn't show:

1. **Hard Refresh:**
   - Windows: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Clear Cache:**
   - Clear browser cache
   - Try incognito/private window

3. **Check Browser Width:**
   - Streamlit hides sidebar on narrow screens
   - Make browser window wider
   - Or use desktop instead of mobile

## What You Should See

When sidebar is visible:

```
┌──────────────────────┐
│  📄 Upload Research  │ ← Purple button
├──────────────────────┤
│ NAVIGATION           │
│ 📄 Current Paper     │
│ 🕒 Recent Files      │
│ 👥 Collaborations    │
└──────────────────────┘
```

## Still Not Working?

### Check Streamlit Cloud Logs:
1. Go to https://share.streamlit.io
2. Find your app
3. Click "Manage app" → "Logs"
4. Look for errors

### Verify Config File:
- Ensure `.streamlit/config.toml` is in your GitHub repo
- Check it has the `[client]` section
- Redeploy if needed

## Quick Test

**On localhost (should work):**
```bash
streamlit run app_v2.py
```
- Sidebar should be visible
- If it works locally but not deployed, it's a deployment config issue

## Most Likely Cause

**The sidebar is collapsed!**
- Just click the hamburger menu (☰) in top-left
- This is the most common issue
- Sidebar is there, just hidden

---

**Updated:** 2026-02-13  
**Config Updated:** Yes (.streamlit/config.toml)  
**Next Step:** Click hamburger menu or redeploy
