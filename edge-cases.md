## What if user dissconnets from google and revokes all access from google but user still exists in our db.
## In /google/scope/callback : Revoke the access_token and refresh_token of previous scopes when user tries to add a new scope on the existing service.
## Rate limiting is not handled. Will be added later.


# Ideas
## partioning the data coming from dynamic node.


# Nodes 
## send_email node/activity
- Concept of  threadId is unhandled
- Attachments messages are unhandled.

## create_email_draft
- Same as send_email
- Response model: {'id': 'r-7563027150901763978', 'message': {'id': '19ddd13cc494eb73', 'threadId': '19ddd13cc494eb73', 'labelIds': ['DRAFT']}}