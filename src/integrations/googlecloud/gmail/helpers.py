import base64
import mimetypes
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Self


class EmailMIMEBuilder:
    def __init__(self):
        self.msg = MIMEMultipart("mixed")

        self.to = []
        self.cc = []
        self.bcc = []

        self.text_body = None
        self.html_body = None

        self.attachments = []
        self.inline_images = []

    # -----------------------------
    # Metadata
    # -----------------------------
    def set_sender(self, sender: str) -> Self:
        self.msg["From"] = sender
        return self

    def set_subject(self, subject: str) -> Self:
        self.msg["Subject"] = subject
        return self

    def add_to(self, recipients) -> Self:
        self.to += self._normalize_list(recipients)
        return self

    def add_cc(self, recipients) -> Self:
        self.cc += self._normalize_list(recipients)
        return self

    def add_bcc(self, recipients) -> Self:
        self.bcc += self._normalize_list(recipients)
        return self

    # -----------------------------
    # Body
    # -----------------------------
    def set_text_body(self, text: str) -> Self:
        self.text_body = text
        return self

    def set_html_body(self, html: str) -> Self:
        self.html_body = html
        return self

    # -----------------------------
    # Attachments
    # -----------------------------
    def add_attachment(self, file_path: str) -> Self:
        self.attachments.append(file_path)
        return self

    def add_attachments(self, file_paths) -> Self:
        self.attachments.extend(file_paths)
        return self

    # -----------------------------
    # Inline Images
    # -----------------------------
    def add_inline_image(self, file_path: str, content_id: str) -> Self:
        self.inline_images.append((file_path, content_id))
        return self

    # -----------------------------
    # Build MIME
    # -----------------------------
    def build(self) -> Self:
        # Set recipients
        self.msg["To"] = ", ".join(self.to)
        if self.cc:
            self.msg["Cc"] = ", ".join(self.cc)
        if self.bcc:
            self.msg["Bcc"] = ", ".join(self.bcc)

        # Body container (alternative)
        if self.text_body or self.html_body:
            alt = MIMEMultipart("alternative")

            if self.text_body:
                alt.attach(MIMEText(self.text_body, "plain"))

            if self.html_body:
                alt.attach(MIMEText(self.html_body, "html"))

            self.msg.attach(alt)

        # Inline images (related)
        if self.inline_images:
            related = MIMEMultipart("related")

            for path, cid in self.inline_images:
                img_part = self._create_file_part(path)
                img_part.add_header("Content-ID", f"<{cid}>")
                img_part.add_header("Content-Disposition", "inline")
                related.attach(img_part)

            self.msg.attach(related)

        # Attachments (mixed)
        for file_path in self.attachments:
            self.msg.attach(self._create_file_part(file_path))

        return self

    # -----------------------------
    # Encode for Gmail API
    # -----------------------------
    def to_gmail_payload(self, thread_id=None) -> dict[str, str]:
        raw = base64.urlsafe_b64encode(self.msg.as_bytes()).decode()

        payload = {"raw": raw}

        if thread_id:
            payload["threadId"] = thread_id

        return payload

    # -----------------------------
    # Helpers
    # -----------------------------
    def _create_file_part(self, file_path) -> MIMEBase:
        content_type, _ = mimetypes.guess_type(file_path)

        if content_type is None:
            content_type = "application/octet-stream"

        main_type, sub_type = content_type.split("/", 1)

        with open(file_path, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())

        encoders.encode_base64(part)

        filename = os.path.basename(file_path)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"'
        )

        return part

    def _normalize_list(self, value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]