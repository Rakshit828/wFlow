GOOGLE_OPENID_SCOPE = ["openid", "email", "profile"]
GOOGLE_EMAIL_ONLY_OPENID_SCOPE = ["openid", "email"]

GOOGLE_SERVICES = {"mail", "gmail", "drive", "sheets", "forms"}
SERVICE_MAPPINGS = {"mail": "gmail"}


GOOGLE_SCOPES = {
    # Gmail service.
    "email": "https://www.googleapis.com/auth/userinfo.email",
    "gmail.fullaccess": "https://mail.google.com/",
    "gmail.readonly": "https://www.googleapis.com/auth/gmail.readonly",
    "gmail.modify": "https://www.googleapis.com/auth/gmail.modify",
    "gmail.compose": "https://www.googleapis.com/auth/gmail.compose",
    "gmail.send": "https://www.googleapis.com/auth/gmail.send",
    "gmail.metadata": "https://www.googleapis.com/auth/gmail.metadata",
    "gmail.labels": "https://www.googleapis.com/auth/gmail.labels",
    "gmail.insert": "https://www.googleapis.com/auth/gmail.insert",
    "gmail.settings.basic": "https://www.googleapis.com/auth/gmail.settings.basic",
    "gmail.settings.sharing": "https://www.googleapis.com/auth/gmail.settings.sharing",
    # GDrive Service.
    # RESTRICTED: Full access to all files and folders
    "drive.fullaccess": "https://www.googleapis.com/auth/drive",
    # RESTRICTED: View and download all files (no edit/delete)
    "drive.readonly": "https://www.googleapis.com/auth/drive.readonly",
    # RECOMMENDED (Non-Sensitive): Access only to files created/opened by this app
    "drive.file": "https://www.googleapis.com/auth/drive.file",
    # SENSITIVE: View/manage metadata (filenames, permissions) but not content
    "drive.metadata": "https://www.googleapis.com/auth/drive.metadata",
    # SENSITIVE: View-only access to metadata
    "drive.metadata.readonly": "https://www.googleapis.com/auth/drive.metadata.readonly",
    # NON-SENSITIVE: Application-specific private data folder
    "drive.appdata": "https://www.googleapis.com/auth/drive.appdata",
    # RESTRICTED: View/modify activity records (who edited what)
    "drive.activity": "https://www.googleapis.com/auth/drive.activity",
    # Google Sheets Service
    # RESTRICTED: Read, edit, create, and delete all your Google Sheets.
    "sheets.fullaccess": "https://www.googleapis.com/auth/spreadsheets",
    # SENSITIVE: Read-only access to your Google Sheets and their properties.
    "sheets.readonly": "https://www.googleapis.com/auth/spreadsheets.readonly",
}

INITIAL_SCOPES_FOR_SERVICE = {
    "gmail": [
        "gmail.send",
        "gmail.compose",
        "gmail.modify",
        "gmail.metadata",
        "gmail.labels",
    ],
    "drive": ["drive.file", "drive.metadata", "drive.activity"],
}

