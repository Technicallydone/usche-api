from .conference_detail_serializer import ConferenceDetailSerializer
from .conference_stats_serializer import ConferenceStatsSerializer
from .conference_serializer import ConferenceSerializer

from .create_conference_serializer import (
    CreateConferenceSerializer,
    CreateVenueSerializer,
    CreateRegistrationFeeSerializer,
    CreateTargetGroupSerializer,
    CreateBankAccountSerializer,
    UpdateConferenceSerializer,
    UpdateRegistrationFeeSerializer,
    UpdateTargetGroupSerializer,
    UpdateBankAccountSerializer,
    SVGUploadSerializer
)

from .schedule_day_serializer import (
    CreateScheduleDaySerializer,
    UpdateScheduleDaySerializer
)

from .schedule_serializer import (
     CreateConferenceScheduleSerializer,
     UpdateConferenceScheduleSerializer
)

from .pre_conference_slider import PreConferenceSliderResponseSerializer
from .conference_slider import ConferenceSliderResponseSerializer
from .slider import SliderBulkUploadSerializer