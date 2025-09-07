import os
from usche_app import settings


def usche_feedback_template(name: str) -> str:
    logo_url = F"{settings.APP_BASE}/media/usche/usche_logo.png"

    html = f"""
        <div style="max-width:600px; margin:auto; padding:20px; border:1px solid #ddd; border-radius:8px; font-family:'Poppins', sans-serif; background-color:#FFF9E6;">
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 20px;">
        <img src="{logo_url}" alt="USCHE Logo" style="height: 50px;" />
        <h1 style="font-size: 28px; font-weight: 700; color: #0864cc; margin: 0;">USCHE</h1>
        </div>


        <!-- Body -->
        <div style="font-size:16px; color:#3C4B64; line-height:1.5; margin-bottom:20px;">
            <p>Dear <strong>{name}</strong>,</p>
            <p>
            We would like to express our sincere appreciation for your participation in the recent USCHE conference.
            You can find more information about the conference at
            <a href="https://usche.ac.tz/" style="color:#0864cc; text-decoration:underline;">https://usche.ac.tz/</a>.
            </p>
            <p>
            The conference was a great success, and now we invite you to provide your valuable feedback.
            Please submit your feedback at
            <a href="https://usche.ac.tz/dashboard/feedback" style="color:#0864cc; text-decoration:underline;">https://usche.ac.tz/dashboard/feedback</a>.
            </p>
        </div>

        <!-- Footer -->
        <div style="font-size:12px; color:#888; border-top:1px solid #eee; padding-top:15px; text-align:center;">
            &copy; 2025 USCHE. All rights reserved.
        </div>
        </div>
    """
    
    print(html) 
    return html