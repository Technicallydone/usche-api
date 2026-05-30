from usche_app import settings

def usche_badge_email_template(name: str) -> str:
    logo_url = f"{settings.APP_BASE}/media/usche/usche_logo.png"

    return f"""
    <div style="
        max-width:600px;
        margin:auto;
        padding:20px;
        border:1px solid #ddd;
        border-radius:8px;
        background:#FFF9E6;
        font-family:Poppins,sans-serif;
    ">

        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:20px;
        ">
            <img src="{logo_url}" style="height:50px;" />
            <h2 style="color:#0864cc;margin:0;">
                USCHE Conference Badge
            </h2>
        </div>

        <p>Dear <strong>{name}</strong>,</p>

        <p>
            Your conference identification badge is attached.
        </p>

        <p>
            Please print and wear this badge throughout the conference.
        </p>

        <p>
            The QR code on the badge will be used for identity verification.
        </p>

        <div style="
            margin-top:20px;
            padding-top:15px;
            border-top:1px solid #ddd;
            text-align:center;
            color:#888;
            font-size:12px;
        ">
            © 2025 USCHE
        </div>

    </div>
    """