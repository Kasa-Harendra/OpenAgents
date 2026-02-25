---
name: mcp-integration
description: Secure integration with MCP services (Gmail, Drive, Calendar, Slack) with authentication, validation, and error handling
license: MIT
compatibility: Requires MCP server access and OAuth credentials
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: call_mcp_service, list_mcp_services, authenticate_mcp
---

# mcp-integration

## Overview

This skill provides comprehensive guidance for integrating with Model Context Protocol (MCP) services. Use this to securely connect to external services like Gmail, Google Drive, Google Calendar, and Slack with proper authentication, input validation, and error handling.

## Core Principles

1. **Security First**: Validate all inputs, never log sensitive data
2. **Authentication**: Handle OAuth flows properly
3. **Confirmation**: Confirm destructive actions with user
4. **Clear Reporting**: Provide readable responses
5. **Error Handling**: Explain API errors clearly

## Supported MCP Services

### Gmail

- **send_email**: Send emails
- **read_emails**: Fetch inbox messages
- **search_emails**: Search by keywords

### Google Drive

- **upload_file**: Upload files to Drive
- **list_files**: List Drive files
- **download_file**: Download file from Drive
- **delete_file**: Remove file from Drive

### Google Calendar

- **create_event**: Add calendar event
- **list_events**: Get upcoming events
- **update_event**: Modify existing event

### Slack (Future)

- **send_message**: Post to channel
- **list_channels**: Get channel list

---

## Instructions

### Step 1: Validate Input Parameters

Before calling any MCP service, validate all parameters:

#### Required Validations

**Service Name**:

- ✅ Must be in allowed list: `gmail`, `drive`, `calendar`, `slack`
- ❌ Reject invalid service names

**Action**:

- ✅ Must be valid for the service
- ❌ Reject unsupported actions

**Parameters**:

- ✅ All required parameters present
- ✅ Parameter types are correct (string, number, etc.)
- ✅ Email addresses are valid format
- ✅ File paths exist (for uploads)

#### Validation Examples

**Valid**:

```json
{
  "service": "gmail",
  "action": "send_email",
  "params": {
    "to": "user@example.com",
    "subject": "Test",
    "body": "Hello"
  }
}
```

**Invalid** (missing parameter):

```json
{
  "service": "gmail",
  "action": "send_email",
  "params": {
    "to": "user@example.com"
    // Missing: subject, body
  }
}
```

---

### Step 2: Check Authentication

Verify MCP service authentication:

#### Authentication Status Check

```json
{
  "tool": "authenticate_mcp",
  "params": {
    "service": "gmail"
  }
}
```

**Responses**:

- ✅ **Authenticated**: Proceed to Step 3
- ❌ **Not Authenticated**: Initiate OAuth flow

#### OAuth Flow (if needed)

1. Generate authentication URL
2. User authorizes application
3. Receive and store OAuth token
4. Retry service call

**User Prompt**:

```
⚠️ Gmail not authorized

To send emails, please authorize access:
1. Visit: https://accounts.google.com/oauth/authorize?...
2. Grant permissions
3. Return here when complete

Waiting for authorization...
```

---

### Step 3: Execute Service Call

Make the MCP service request:

```json
{
  "tool": "call_mcp_service",
  "params": {
    "service": "gmail",
    "action": "send_email",
    "params": {
      "to": "recipient@example.com",
      "subject": "Project Update",
      "body": "Here's the latest update..."
    }
  }
}
```

**Service Response Structure**:

```json
{
  "success": true,
  "data": {...},
  "message": "Email sent successfully"
}
```

---

### Step 4: Process and Format Response

Transform API response to user-friendly format:

#### Success Response

```
✅ Email sent successfully

To: recipient@example.com
Subject: Project Update
Sent: 2026-02-13 23:00:00

Message ID: <abc123@gmail.com>
```

#### Error Response

```
❌ Failed to send email

Error: Invalid recipient email address

Explanation:
The email address 'invalid-email' is not in a valid format.

Suggested Fix:
- Use format: username@domain.com
- Verify the email address is correct
```

---

### Step 5: Security Considerations

#### Never Log Sensitive Data

❌ Don't log:

- Email contents
- OAuth tokens
- File contents
- Private calendar details

✅ Do log:

- Operation type
- Success/failure status
- Error codes (not sensitive errors)

#### Confirm Destructive Actions

For operations like:

- Deleting files
- Removing calendar events
- Bulk email sends

**Prompt user**:

```
⚠️ Destructive operation requested

Action: Delete file from Google Drive
File: important-document.pdf

Are you sure? This cannot be undone.
Please confirm: [yes/no]
```

---

## MCP Service Examples

### Example 1: Send Gmail Email

**Request**: "Send email to john@example.com about meeting"

**Validation**:

```
✅ Service: gmail (valid)
✅ Action: send_email (supported)
✅ Parameters:
   - to: john@example.com (valid email)
   - subject: (will be generated)
   - body: (will be generated)
```

**Execution**:

```json
{
  "tool": "call_mcp_service",
  "params": {
    "service": "gmail",
    "action": "send_email",
    "params": {
      "to": "john@example.com",
      "subject": "Meeting Discussion",
      "body": "Hi John,\n\nLet's discuss the meeting details.\n\nBest regards"
    }
  }
}
```

**Response**:

```
✅ Email sent successfully

To: john@example.com
Subject: Meeting Discussion
Sent: 2026-02-13 23:00:00 UTC
Message ID: <msg_abc123@gmail.com>

The email has been delivered to john@example.com inbox.
```

---

### Example 2: Upload File to Google Drive

**Request**: "Upload report.pdf to Google Drive"

**Validation**:

```
✅ Service: drive (valid)
✅ Action: upload_file (supported)
✅ Parameters:
   - file_path: ./report.pdf (exists)
   - destination: / (valid path)
```

**Execution**:

```json
{
  "tool": "call_mcp_service",
  "params": {
    "service": "drive",
    "action": "upload_file",
    "params": {
      "file_path": "./report.pdf",
      "destination": "/Documents",
      "name": "Monthly Report - Feb 2026.pdf"
    }
  }
}
```

**Response**:

```
✅ File uploaded successfully

File: Monthly Report - Feb 2026.pdf
Location: Google Drive > Documents
Size: 2.3 MB
Drive Link: https://drive.google.com/file/d/abc123

The file is now accessible in your Google Drive.
```

---

### Example 3: List Upcoming Calendar Events

**Request**: "Show my calendar events for next week"

**Validation**:

```
✅ Service: calendar (valid)
✅ Action: list_events (supported)
✅ Parameters:
   - time_min: 2026-02-14 (calculated)
   - time_max: 2026-02-21 (calculated)
```

**Execution**:

```json
{
  "tool": "call_mcp_service",
  "params": {
    "service": "calendar",
    "action": "list_events",
    "params": {
      "time_min": "2026-02-14T00:00:00Z",
      "time_max": "2026-02-21T00:00:00Z",
      "max_results": 10
    }
  }
}
```

**Response**:

```
📅 Upcoming Events (Feb 14-21, 2026)

1. Team Standup
   📆 Mon, Feb 14 - 9:00 AM (30 min)
   📍 Video Call

2. Project Review
   📆 Wed, Feb 16 - 2:00 PM (1 hour)
   📍 Conference Room A
   👥 5 attendees

3. Client Meeting
   📆 Fri, Feb 18 - 10:00 AM (45 min)
   📍 Zoom

Total: 3 events
```

---

## Error Handling

### Error 1: Authentication Failed

**Scenario**: OAuth token expired or invalid

**Response**:

```
❌ Authentication error

Service: Gmail
Error: OAuth token expired

Explanation:
Your authorization for Gmail has expired and needs to be renewed.

Suggested Fix:
1. Re-authorize Gmail access
2. Visit: [auth_url]
3. Grant permissions
4. Retry the operation

Would you like to re-authorize now?
```

---

### Error 2: Invalid Parameters

**Scenario**: Missing required parameter

**Response**:

```
❌ Invalid parameters

Service: Gmail
Action: send_email

Missing required parameters:
- subject (required)
- body (required)

Provided parameters:
- to: user@example.com ✅

Suggested Fix:
Please provide the missing parameters:
- Email subject line
- Email body content
```

---

### Error 3: API Rate Limit

**Scenario**: Too many requests to service

**Response**:

```
❌ Rate limit exceeded

Service: Gmail
Error: Quota exceeded for API requests

Explanation:
Gmail API has a daily limit of 500 emails.
You've reached this limit for today.

Suggested Fix:
- Wait until tomorrow (quota resets at midnight UTC)
- Use a different Gmail account
- Contact Google to request quota increase

Current usage: 500/500
Reset time: 2026-02-14 00:00:00 UTC (5 hours)
```

---

### Error 4: Permission Denied

**Scenario**: Service action not authorized

**Response**:

```
❌ Permission denied

Service: Drive
Action: delete_file

Explanation:
The application doesn't have permission to delete files.
You granted read-only access during authorization.

Suggested Fix:
1. Re-authorize with additional permissions
2. Grant "delete" permission when prompted
3. Retry the operation

Required permissions:
- drive.file (current) ✅
- drive.file.delete (missing) ❌
```

---

## Service-Specific Guidelines

### Gmail Best Practices

- Validate email addresses before sending
- Include meaningful subject lines
- Keep emails concise and clear
- Respect daily sending limits (500/day)
- Never send spam or unsolicited emails

### Google Drive Best Practices

- Organize files in folders
- Use descriptive filenames
- Check available storage before uploads
- Confirm before deleting files
- Share files with appropriate permissions

### Google Calendar Best Practices

- Include clear event titles
- Set appropriate time zones
- Add meaningful descriptions
- Invite only necessary attendees
- Set reminders for important events

---

## Security Checklist

Before every MCP operation:

- ✅ Validate service name
- ✅ Validate action name
- ✅ Validate all parameters
- ✅ Check authentication status
- ✅ Sanitize user inputs
- ✅ Confirm destructive operations
- ✅ Don't log sensitive data
- ✅ Handle errors gracefully
- ✅ Report clearly to user

---

## Advanced Example: Batch Email Send

**Request**: "Send project update email to team (3 members)"

**Safety Check**:

```
⚠️ Batch email operation

Recipients: 3
- user1@example.com
- user2@example.com
- user3@example.com

Subject: Project Update - February 2026

Confirm sending to all recipients? [yes/no]
```

**After Confirmation**:

```
Sending emails... (3 total)

✅ Sent to user1@example.com
✅ Sent to user2@example.com
✅ Sent to user3@example.com

Summary:
- Success: 3/3
- Failed: 0/3
- Total time: 2.3 seconds

All emails sent successfully.
```

---

## Troubleshooting

**Q: "OAuth flow fails"**
**A**: Check redirect URI matches registered OAuth app, verify client ID/secret

**Q: "API calls timing out"**
**A**: Check internet connection, verify MCP server is running, check service status

**Q: "Permission errors despite authorization"**
**A**: Re-authorize with correct permission scopes, check OAuth consent screen settings

**Q: "Rate limit errors"**
**A**: Implement exponential backoff, spread requests over time, monitor quota usage
