from .conference_detail_serializer import ConferenceDetailSerializer
from .request_join_conference import RequestJoinConferenceSerializer
from .conference_stats_serializer import ConferenceStatsSerializer
from .conference_serializer import ConferenceSerializer

from .create_conference_serializer import (
    CreateConferenceSerializer,
    CreateVenueSerializer,
    CreateRegistrationFeeSerializer,
    CreateTargetGroupSerializer,
    CreateBankAccountSerializer,
    CreateScheduleDaySerializer,
    CreateConferenceScheduleSerializer,
    UpdateConferenceSerializer,
    UpdateRegistrationFeeSerializer,
    UpdateTargetGroupSerializer,
    UpdateBankAccountSerializer,
    UpdateScheduleDaySerializer,
    UpdateConferenceScheduleSerializer,
    SVGUploadSerializer
)

from .pre_conference_slider import PreConferenceSliderResponseSerializer
from .conference_slider import ConferenceSliderResponseSerializer
from .slider import SliderBulkUploadSerializer