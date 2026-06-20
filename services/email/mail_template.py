# services/email/mail_template.py
from typing import List, Optional

class EmailTemplate:
    """
    Reusable card-style email template for USChE emails.
    Supports dynamic greeting, body lines, button, and salutations.
    """

    def __init__(self, subject: str, to: str):
        self.subject = subject
        self.to = to
        self.greeting: Optional[str] = None
        self.lines: List[str] = []
        self.button_text: Optional[str] = None
        self.button_url: Optional[str] = None
        self.salutations: List[str] = []
        self.footer_text: str = "© 2026 Your Company. All rights reserved."

    # Set greeting
    def set_greeting(self, greeting: str) -> "EmailTemplate":
        self.greeting = greeting
        return self

    # Add body lines
    def add_lines(self, lines: List[str]) -> "EmailTemplate":
        self.lines.extend(lines)
        return self

    # Add salutations
    def add_salutations(self, salutations: List[str]) -> "EmailTemplate":
        self.salutations.extend(salutations)
        return self

    # Set call-to-action button
    def set_button(self, text: str, url: str) -> "EmailTemplate":
        self.button_text = text
        self.button_url = url
        return self

    # Set footer text
    def set_footer(self, footer_text: str) -> "EmailTemplate":
        self.footer_text = footer_text
        return self

    # Build the full HTML
    def build(self) -> str:
        # Build body lines HTML
        body_lines_html = ""
        for line in self.lines:
            body_lines_html += f'<p style="color:#555;font-size:15px;line-height:1.7;margin:0 0 20px;">{line}</p>\n'

        # Build button HTML
        button_html = ""
        if self.button_text and self.button_url:
            button_html = f'''
            <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
            <tr>
                <td style="background:linear-gradient(135deg,#d4a039,#c4912a);border-radius:8px;padding:14px 36px;text-align:center;">
                    <a href="{self.button_url}" style="color:#fff;text-decoration:none;font-size:15px;font-weight:bold;font-family:sans-serif;">
                        {self.button_text} →
                    </a>
                </td>
            </tr>
            </table>
            '''

        # Build salutations HTML
        salutations_html = ""
        if self.salutations:
            salutations_html = '<p style="margin-top:20px; color:#555; font-size:15px; line-height:1.7;">' + "<br>".join(self.salutations) + "</p>"

        # Greeting fallback
        greeting_html = self.greeting if self.greeting else "Welcome aboard! 🎉"

        # Full HTML
        html = f"""
            <!doctype html>
            <html>
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            </head>
            <body
                style="
                margin: 0;
                padding: 0;
                background-color: #f8f6f3;
                font-family: Georgia, serif;
                "
            >
                <table
                width="100%"
                cellpadding="0"
                cellspacing="0"
                style="background-color: #f8f6f3; padding: 40px 20px"
                >
                <tr>
                    <td align="center">
                    <table
                        width="600"
                        cellpadding="0"
                        cellspacing="0"
                        style="
                        background-color: #ffffff;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
                        "
                    >
                        <tr>
                        <td
                            style="
                            background: linear-gradient(135deg, #1a1a2e, #16213e);
                            padding: 48px 40px;
                            text-align: center;
                            "
                        >
                            <h1 style="color: #ffffff; font-size: 28px; margin: 0 0 8px">
                            {greeting_html}
                            </h1>
                            <p style="color: #a0a0b8; font-size: 15px; margin: 0">
                            Important information from USChE
                            </p>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding: 40px">
                            {body_lines_html} {button_html} {salutations_html}
                        </td>
                        </tr>
                        <tr>
                        <td
                            style="
                            padding: 24px 40px;
                            background: #fafaf8;
                            text-align: center;
                            border-top: 1px solid #eee;
                            "
                        >
                            <p style="color: #999; font-size: 12px; margin: 0">
                            {self.footer_text}
                            </p>
                            <p style="color: #bbb; font-size: 11px; margin: 8px 0 0">
                            <a href="#" style="color: #bbb">Unsubscribe</a> ·
                            <a href="#" style="color: #bbb">Preferences</a>
                            </p>
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>
                </table>
            </body>
            </html>

        """
        return html
