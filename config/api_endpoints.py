from usche_app import settings


class APIEndpoints:
    """
    Centralized API endpoint registry.
    All backend-generated URLs should be defined here.
    """

    # =========================
    # BASE
    # =========================
    BASE = settings.APP_BASE.rstrip("/")

    # =========================
    # SPEAKERS
    # =========================
    SPEAKER_IMAGE = f"{BASE}/api/v1/speaker/images/speaker-image"

    # =========================
    # SPONSORS
    # =========================
    SPONSOR_LOGO = f"{BASE}/api/v1/sponsor/logo/sponsor-logo"

    # =========================
    # ABSTRACTS
    # =========================
    ABSTRACT_DOCUMENT = f"{BASE}/api/v1/abstracts"

    # =========================
    # PAYMENTS
    # =========================
    PAYMENT_SLIP = f"{BASE}/api/v1/payment/payments/payment-slip"

    # =========================
    # CONFERENCE
    # =========================
    CONFERENCE = f"{BASE}/api/v1/conference"

    PRE_CONFERENCE_SLIDERS = f"{BASE}/api/v1/conference/pre-sliders"

    CONFERENCE_SLIDERS = f"{BASE}/api/v1/conference/sliders"

    # =========================
    # CERTIFICATES
    # =========================
    CERTIFICATE_BACKGROUND = f"{BASE}/api/v1/conference"