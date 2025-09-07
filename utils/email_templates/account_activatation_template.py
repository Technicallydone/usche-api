from usche_app import settings


def usche_account_activation_template(title: str, last_name: str, activation_url: str) -> str:
    # Assuming usche_logo.png is in a media folder accessible via APP_BASE/media/usche/
    # If not, adjust logo_url accordingly or remove if not needed for this email.
    # For a simple activation email, a logo might not be strictly necessary,
    # but I'll include it for consistency with your feedback template.
    try:
        logo_url = F"{settings.FRONTEND_BASE_URL}/media/usche/usche_logo.png"
    except AttributeError:
        # Fallback if settings.APP_BASE is not defined or logo not used
        logo_url = "" # Or a placeholder image URL

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Account Activation</title>
        <style>
          body {{
            font-family: "Poppins", sans-serif;
            background-color: #fff9e6; /* Light yellow background */
            margin: 0;
            padding: 0;
            color: #3c4b64; /* Dark blue-gray text */
          }}
          .container {{
            max-width: 600px;
            margin: 20px auto; /* Add some top/bottom margin */
            padding: 20px;
            background-color: #ffffff; /* White card background */
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Subtle shadow */
          }}
          .header-section {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee; /* Separator line */
          }}
          .header-text {{
            font-size: 24px;
            font-weight: bold;
            color: #0864cc; /* Blue header text */
            margin: 0;
          }}
          .logo-img {{
            height: 50px; /* Adjust logo size */
          }}
          .message {{
            font-size: 16px;
            line-height: 1.6; /* Improved readability */
            margin-top: 15px;
          }}
          .message p {{
            margin-bottom: 10px; /* Space between paragraphs */
          }}
          .cta-button {{
            display: inline-block;
            padding: 10px 20px;
            background-color: #0864cc; /* Blue button */
            color: white !important; /* Ensure white text */
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
            margin-bottom: 20px; /* Space below button */
            font-size: 16px;
            font-weight: bold;
          }}
          .footer {{
            font-size: 14px;
            color: #f4a900; /* Orange footer text */
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee; /* Separator line */
          }}
          .footer p {{
            margin: 5px 0;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header-section">
            <img src="{logo_url}" alt="USCHE Logo" class="logo-img" />
            <div class="header-text">USCHE</div>
          </div>
          <div class="message">
            <p>Dear <strong>{title} {last_name}</strong>,</p>
            <p>Please activate your account by clicking the link below:</p>
            <a href="{activation_url}" class="cta-button">Activate Account</a>
            <p>
              This link will expire in 1 hour. If you did not request this, please
              ignore this email.
            </p>
          </div>
          <div class="footer">
            <p>Regards,</p>
            <p>USCHe</p>
          </div>
        </div>
      </body>
    </html>
    """

    return html

# Example usage (assuming settings.py has APP_BASE defined)
# In your Django views or management commands:
# from usche_app.settings import APP_BASE
# from .utils import usche_account_activation_template # Assuming this function is in a 'utils.py'
#
# activation_link = "http://yourdomain.com/activate/some_token/"
# email_html = usche_account_activation_template(
#     title="Mr.",
#     last_name="Doe",
#     activation_url=activation_link
# )
#
# # You would then use this 'email_html' with Django's EmailMessage
# from django.core.mail import EmailMessage
# email = EmailMessage(
#     'Activate Your USCHE Account',
#     email_html,
#     'noreply@usche.ac.tz', # From email
#     ['user@example.com'], # To email
# )
# email.content_subtype = "html" # Main content is HTML
# email.send()