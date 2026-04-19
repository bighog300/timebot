# PHASE 2: CLOUD INTEGRATIONS - COMPLETE GUIDE

## Overview

**Phase 2 Goal**: Connect to Gmail, Google Drive, and Dropbox to automatically sync and process documents from cloud services.

**Timeline**: 8 weeks (4 sprints × 2 weeks each)  
**Prerequisites**: Phase 1 completed (backend with async processing)

---

## What You'll Build

By the end of Phase 2, users can:
1. **Connect their Gmail** → Auto-import emails with attachments
2. **Connect Google Drive** → Auto-sync all files
3. **Connect Dropbox** → Auto-sync all files
4. **Auto-process everything** → All synced documents go through your AI pipeline

---

## Sprint Breakdown

### **Sprint 5: OAuth & Authentication** (Weeks 9-10)
Build the authentication foundation

**Key Deliverables:**
- OAuth 2.0 flows for Google, Dropbox, Microsoft
- Secure token storage with encryption
- Token refresh mechanism
- Connection management API

**Files Created:**
- `app/core/encryption.py` - Token encryption
- `app/services/oauth/base.py` - Base OAuth handler
- `app/services/oauth/google_oauth.py` - Google OAuth
- `app/services/oauth/dropbox_oauth.py` - Dropbox OAuth
- `app/services/oauth/microsoft_oauth.py` - Microsoft OAuth  
- `app/services/oauth/token_manager.py` - Token management
- `app/api/v1/connections.py` - Connection CRUD
- `app/api/v1/oauth_callbacks.py` - OAuth callbacks

**Key Features:**
- Click "Connect Gmail" → OAuth flow → Tokens stored securely
- Auto-refresh expired tokens
- Revoke access anytime

---

### **Sprint 6: Gmail Integration** (Weeks 11-12)
Connect to Gmail and import emails

**Key Deliverables:**
- Gmail API client
- Email fetching with attachments
- Incremental sync (only new emails)
- Thread/conversation handling
- Email-to-document conversion

**Files Created:**
- `app/services/integrations/gmail_client.py` - Gmail API wrapper
- `app/services/integrations/gmail_parser.py` - Email parsing
- `app/services/integrations/gmail_sync.py` - Sync logic
- `app/workers/tasks.py` - Gmail sync tasks (UPDATE)

**Key Features:**
- Sync last 30 days of emails on connect
- Extract attachments as documents
- Incremental sync every 15 minutes
- Email body saved as document text
- Track conversation threads

---

### **Sprint 7: Google Drive Integration** (Weeks 13-14)
Connect to Google Drive and sync files

**Key Deliverables:**
- Google Drive API client
- File discovery and download
- Change detection (Drive webhooks)
- Folder structure mapping
- Shared drive support

**Files Created:**
- `app/services/integrations/gdrive_client.py` - Drive API wrapper
- `app/services/integrations/gdrive_sync.py` - Sync logic
- `app/services/integrations/gdrive_watcher.py` - Change notifications
- `app/workers/tasks.py` - Drive sync tasks (UPDATE)

**Key Features:**
- Sync entire Drive on connect
- Detect file changes automatically
- Download only new/modified files
- Support My Drive + Shared Drives
- Incremental sync

---

### **Sprint 8: Dropbox Integration** (Weeks 15-16)
Connect to Dropbox and sync files

**Key Deliverables:**
- Dropbox API client
- File sync logic
- Webhook for change notifications
- Team folders support
- Version tracking

**Files Created:**
- `app/services/integrations/dropbox_client.py` - Dropbox API wrapper
- `app/services/integrations/dropbox_sync.py` - Sync logic
- `app/services/integrations/dropbox_webhook.py` - Webhook handler
- `app/api/v1/webhooks.py` - Webhook endpoints
- `app/workers/tasks.py` - Dropbox sync tasks (UPDATE)

**Key Features:**
- Sync entire Dropbox on connect
- Real-time change detection via webhook
- Download only changed files
- Support personal + team folders
- File versioning

---

## High-Level Architecture

```
┌─────────────────┐
│  User clicks    │
│ "Connect Gmail" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OAuth Flow     │
│  1. Redirect    │
│  2. Grant       │
│  3. Callback    │
│  4. Store token │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sync Service   │
│  - Fetch emails │
│  - Download     │
│  - Queue tasks  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Document Queue  │
│ (from Phase 1)  │
│  - Extract text │
│  - AI analysis  │
│  - Categorize   │
└─────────────────┘
```

---

## Complete File Structure

```
backend/
├── app/
│   ├── core/
│   │   └── encryption.py              [Sprint 5 - NEW]
│   │
│   ├── services/
│   │   ├── oauth/                     [Sprint 5 - NEW]
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── google_oauth.py
│   │   │   ├── dropbox_oauth.py
│   │   │   ├── microsoft_oauth.py
│   │   │   └── token_manager.py
│   │   │
│   │   └── integrations/              [Sprints 6-8 - NEW]
│   │       ├── __init__.py
│   │       ├── gmail_client.py        [Sprint 6]
│   │       ├── gmail_parser.py        [Sprint 6]
│   │       ├── gmail_sync.py          [Sprint 6]
│   │       ├── gdrive_client.py       [Sprint 7]
│   │       ├── gdrive_sync.py         [Sprint 7]
│   │       ├── gdrive_watcher.py      [Sprint 7]
│   │       ├── dropbox_client.py      [Sprint 8]
│   │       ├── dropbox_sync.py        [Sprint 8]
│   │       └── dropbox_webhook.py     [Sprint 8]
│   │
│   ├── api/v1/
│   │   ├── connections.py             [Sprint 5 - NEW]
│   │   ├── oauth_callbacks.py         [Sprint 5 - NEW]
│   │   └── webhooks.py                [Sprint 8 - NEW]
│   │
│   └── workers/
│       └── tasks.py                   [UPDATE in each sprint]
│
├── .env.example                       [UPDATE with OAuth keys]
└── requirements.txt                   [UPDATE with API clients]
```

---

## Environment Variables Needed

```bash
# Google OAuth
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback

# Dropbox OAuth
DROPBOX_APP_KEY=...
DROPBOX_APP_SECRET=...
DROPBOX_REDIRECT_URI=http://localhost:8000/api/v1/oauth/dropbox/callback

# Microsoft OAuth (optional for OneDrive)
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/oauth/microsoft/callback

# Token Encryption
TOKEN_ENCRYPTION_KEY=generate_with_Fernet
```

---

## Getting OAuth Credentials

### Google (Gmail + Drive)
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable APIs: Gmail API, Google Drive API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/api/v1/oauth/google/callback`
6. Copy Client ID and Secret

### Dropbox
1. Go to https://www.dropbox.com/developers/apps
2. Create new app
3. Choose "Scoped access"
4. Add permissions: files.content.read
5. Add redirect URI: `http://localhost:8000/api/v1/oauth/dropbox/callback`
6. Copy App key and Secret

### Microsoft (OneDrive)
1. Go to https://portal.azure.com/
2. Azure Active Directory → App registrations
3. New registration
4. Add redirect URI: `http://localhost:8000/api/v1/oauth/microsoft/callback`
5. API permissions: Files.Read.All
6. Copy Application ID and Secret

---

## Implementation Strategy

### Option 1: Sprint by Sprint (Recommended)
Build each sprint in order:
1. Complete Sprint 5 → Test OAuth flows work
2. Complete Sprint 6 → Test Gmail sync works
3. Complete Sprint 7 → Test Drive sync works
4. Complete Sprint 8 → Test Dropbox sync works

### Option 2: Vertical Slice
Build one integration end-to-end first:
1. Sprint 5 OAuth (just Google)
2. Sprint 6 Gmail
3. Test thoroughly
4. Then add Drive and Dropbox

### Option 3: All at Once
Implement all sprints together (risky, harder to debug)

---

## Key Implementation Patterns

### OAuth Flow Pattern
```python
# 1. User clicks "Connect Gmail"
GET /api/v1/connections/google/authorize
→ Returns: {auth_url: "https://accounts.google.com/..."}

# 2. User redirects to Google, grants permission

# 3. Google redirects back
GET /api/v1/oauth/google/callback?code=...
→ Exchange code for tokens
→ Store encrypted tokens
→ Return: {status: "connected"}
```

### Sync Pattern
```python
# Periodic task (every 15 minutes)
@celery_app.task
def sync_gmail(connection_id):
    # 1. Get valid token (auto-refresh if needed)
    token = token_manager.get_valid_token(db, connection)
    
    # 2. Fetch new emails
    emails = gmail_client.fetch_emails(token, since=last_sync)
    
    # 3. For each email:
    for email in emails:
        # Save email as document
        doc = create_document_from_email(email)
        
        # Queue for processing
        process_document_task.delay(doc.id)
    
    # 4. Update sync state
    connection.last_sync_date = now()
```

### Change Detection Pattern
```python
# For Drive and Dropbox
@celery_app.task
def check_drive_changes(connection_id):
    # 1. Get changes since last sync token
    changes = gdrive_client.get_changes(token, start_token)
    
    # 2. Process changes
    for change in changes:
        if change.type == 'file_added':
            download_and_process(change.file_id)
        elif change.type == 'file_modified':
            re_download_and_process(change.file_id)
        elif change.type == 'file_deleted':
            mark_document_deleted(change.file_id)
    
    # 3. Save new sync token
    connection.sync_state['page_token'] = changes.new_start_page_token
```

---

## Testing Checklist

### Sprint 5 Testing
- [ ] GET `/api/v1/connections/google/authorize` returns auth URL
- [ ] OAuth callback works and stores tokens
- [ ] Tokens are encrypted in database
- [ ] Can refresh expired tokens
- [ ] Can disconnect and revoke tokens

### Sprint 6 Testing
- [ ] Connect Gmail account
- [ ] Initial sync imports last 30 days emails
- [ ] Attachments extracted as documents
- [ ] Incremental sync gets new emails
- [ ] Email threads tracked correctly

### Sprint 7 Testing
- [ ] Connect Google Drive account
- [ ] Initial sync imports all files
- [ ] Change detection works
- [ ] Modified files re-sync
- [ ] Shared drives accessible

### Sprint 8 Testing
- [ ] Connect Dropbox account
- [ ] Initial sync imports all files
- [ ] Webhook receives change notifications
- [ ] Changed files re-sync
- [ ] Team folders accessible

---

## Common Issues & Solutions

**Issue**: "OAuth redirect_uri_mismatch"
**Solution**: Exact match required. Check http vs https, trailing slash, port number

**Issue**: "Insufficient permissions"
**Solution**: Request correct scopes during OAuth, may need to re-authenticate

**Issue**: "Token expired" errors
**Solution**: Implement auto-refresh in token_manager.get_valid_token()

**Issue**: "Rate limit exceeded"
**Solution**: Add exponential backoff, respect API quotas

**Issue**: "Duplicate documents on sync"
**Solution**: Check source_id uniqueness constraint, track synced items

---

## Performance Considerations

### Sync Efficiency
- **Gmail**: Sync only since last sync date
- **Drive**: Use changes API, not full file list
- **Dropbox**: Use cursor-based pagination

### Rate Limiting
- Google: 1,000 requests/100 seconds
- Dropbox: 1,000 requests/5 minutes
- Solution: Implement exponential backoff

### Storage
- Don't duplicate files - use source_id to deduplicate
- Store original in cloud, only cache locally if needed
- Clean up old sync logs regularly

---

## Success Metrics

### Sprint 5 Success
- Can authenticate with all 3 services
- Tokens stored securely
- Auto-refresh works

### Sprint 6 Success
- 100+ emails synced from Gmail
- Attachments extracted correctly
- Incremental sync < 1 minute

### Sprint 7 Success  
- 100+ files synced from Drive
- Change detection < 5 minutes
- Shared drives work

### Sprint 8 Success
- 100+ files synced from Dropbox
- Webhook detects changes instantly
- Team folders work

### Phase 2 Complete
- All 3 services connected
- 1000+ documents synced
- Auto-sync every 15 minutes
- All synced docs processed by AI

---

## Next Steps

After Phase 2, you'll have:
- ✅ Complete backend with AI processing
- ✅ Cloud service integrations (Gmail, Drive, Dropbox)
- ✅ Auto-sync from cloud sources
- ✅ Everything processed through AI pipeline

**Then move to Phase 3**: Search & Intelligence
- Semantic search
- Document relationships
- Insights generation
- Timeline visualization

**Or Phase 4**: Frontend
- React UI
- Timeline view
- Search interface
- Connection management

---

## Recommended Approach for Your AI Coding Assistant

### Step 1: Sprint 5 Foundation
```
"Implement Sprint 5: OAuth & Authentication

Create these services:
1. Token encryption with Fernet
2. Base OAuth handler class
3. Google OAuth handler (Gmail + Drive)
4. Dropbox OAuth handler
5. Microsoft OAuth handler
6. Token manager with auto-refresh
7. Connections API endpoints
8. OAuth callback handlers

Include:
- Secure token storage
- Auto-refresh mechanism
- Connection management API
- OAuth flow testing
"
```

### Step 2: Sprint 6 Gmail
```
"Implement Sprint 6: Gmail Integration

Build on Sprint 5 OAuth to add:
1. Gmail API client
2. Email fetching with pagination
3. Attachment extraction
4. Email-to-document conversion
5. Incremental sync task
6. Background sync worker

Test by:
- Connecting Gmail account
- Syncing last 30 days
- Extracting attachments
- Running incremental sync
"
```

### Step 3-4: Repeat for Drive and Dropbox

---

**Ready to start Phase 2?** 

You have everything documented. Choose your approach and let's build cloud integrations! 🚀
