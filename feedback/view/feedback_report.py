import logging
from typing import cast

from django.http import HttpRequest
from feedback.enums.question_type import QuestionTypeEnum
from feedback.models import Question, FeedbackAnswer
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from feedback.serializers import QuestionReportSerializer
from user.enums.role import ROLE
from user.models import User

logger = logging.getLogger(__name__)


class FeedbackReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        method='get',
        operation_summary="Generate feedback report by conference ID",
        operation_description="Returns a report summarizing multiple-choice option counts and free text responses for a given conference.",
        tags=["Feedback"],
        manual_parameters=[
            openapi.Parameter(
                name="conference_id",
                in_=openapi.IN_QUERY,
                description="UUID of the conference",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Feedback report generated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "question_id": openapi.Schema(type=openapi.TYPE_STRING),
                            "question_text": openapi.Schema(type=openapi.TYPE_STRING),
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                enum=["multiple-choice", "text"]
                            ),
                            "options": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "option_id": openapi.Schema(type=openapi.TYPE_STRING),
                                        "option_text": openapi.Schema(type=openapi.TYPE_STRING),
                                        "count": openapi.Schema(type=openapi.TYPE_INTEGER)
                                    }
                                )
                            ),
                            "answers": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                                        "submitted_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time")
                                    }
                                )
                            )
                        }
                    )
                )
            ),
            400: openapi.Response(description="Bad request: missing conference_id"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    @action(detail=False, methods=["get"], url_path="conference-report")
    def get_conference_report(self, request: HttpRequest):
        user = cast(User, request.user)

        if not request.user.is_authenticated and user.role not in [ROLE.ORGANIZER.value, ROLE.BURSAR.value, ROLE.ADMIN.value]:
            return Response(
                {"detail": "You are not authorized to perform this task"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        conference_id = request.GET.get("conference_id")

        if not conference_id:
            return Response({"detail": "conference_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            questions = Question.objects.filter(conference_id=conference_id).prefetch_related("options", "answers")
            report_data = []

            for q in questions:
                if q.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
                    option_counts = []
                    for option in q.options.all():
                        count = FeedbackAnswer.objects.filter(question=q, option=option).count()
                        option_counts.append({
                            "option_id": option.id,
                            "option_text": option.option,
                            "count": count
                        })
                    report_data.append({
                        "question_id": q.id,
                        "question_text": q.question,
                        "type": q.type,
                        "options": option_counts
                    })

                elif q.type == QuestionTypeEnum.TEXT.value:
                    answers = FeedbackAnswer.objects.filter(
                        question=q,
                        text__isnull=False
                    ).exclude(text="").values("text", "submitted_at")
                    report_data.append({
                        "question_id": q.id,
                        "question_text": q.question,
                        "type": q.type,
                        "answers": list(answers)
                    })

            serializer = QuestionReportSerializer(report_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error generating feedback report")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
