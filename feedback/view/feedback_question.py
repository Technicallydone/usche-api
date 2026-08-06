import logging

from feedback.enums.question_type import QuestionTypeEnum
from feedback.models import Option
from feedback.utils import generate_feedback_report_pdf
from rest_framework import permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action

from conference.models import Conference
from feedback.models import Question, FeedbackAnswer
from feedback.serializers import (
    CreateQuestionSerializer,
    QuestionFilterQuerySerializer,
    QuestionSerializer,
    UpdateQuestionSerializer,
    SubmitFeedbackSerializer,
    FeedbackReportFilterQuerySerializer,
    FeedbackAnswerDetailSerializer
)
from user.enums.permission_enums import AppPermissionEnum
from user.permissions import HasAppPermission
from django.db import transaction
from django.http import FileResponse

logger = logging.getLogger(__name__)


class FeedbackQuestionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny, HasAppPermission]

    permission_mapping = {
        # "list": AppPermissionEnum.READ_FEEDBACK_QUESTIONS.value,
        "retrieve": AppPermissionEnum.READ_FEEDBACK_QUESTIONS.value,
        "create": AppPermissionEnum.CREATE_FEEDBACK_QUESTIONS.value,
        "update": AppPermissionEnum.UPDATE_FEEDBACK_QUESTIONS.value,
        "destroy": AppPermissionEnum.DELETE_FEEDBACK_QUESTIONS.value,
        "delete_option": AppPermissionEnum.DELETE_FEEDBACK_OPTIONS.value,
        "view_responses": AppPermissionEnum.READ_FEEDBACK_RESPONSES.value,
        "export_feedback_pdf": AppPermissionEnum.READ_FEEDBACK_RESPONSES.value,
    }
    
    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<conference_id>[^/.]+)/pdf",
    )
    def export_feedback_pdf(self, request: Request, conference_id=None):
        try:
            conference = Conference.objects.get(conference_id=conference_id)

            pdf = generate_feedback_report_pdf.generate_feedback_report_pdf(conference=conference)

            filename = f"{conference.conference_name}-feedback-report.pdf"

            return FileResponse(
                pdf,
                as_attachment=True,
                filename=filename,
                content_type="application/pdf",
            )

        except Conference.DoesNotExist:
            logger.warning(
                f"Export PDF failed: Conference '{conference_id}' not found."
            )
            return Response(
                {"detail": "Conference not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(
                f"Error generating feedback PDF for conference {conference_id}: {str(e)}",
                exc_info=True,
            )
            return Response(
                {"detail": "Failed to generate feedback report PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    # -----------------------------------
    # VIEW FEEDBACK REPORT (PAGINATED ANSWERS)
    # -----------------------------------
    @action(
        detail=False,
        methods=["get"],
        url_path="responses",
    )
    def view_responses(self, request: Request):
        filter_serializer = FeedbackReportFilterQuerySerializer(
            data=request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        conference_id = filter_serializer.validated_data.get("conference_id")
        created_from = filter_serializer.validated_data.get("created_from")
        created_to = filter_serializer.validated_data.get("created_to")

        try:
            answer_filters = {}
            if conference_id:
                answer_filters["question__conference_id"] = conference_id
            if created_from:
                answer_filters["submitted_at__gte"] = created_from
            if created_to:
                answer_filters["submitted_at__lte"] = created_to

            answers_qs = (
                FeedbackAnswer.objects
                .filter(**answer_filters)
                .select_related("question", "option")
                .order_by("-submitted_at")
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(
                answers_qs,
                request,
            )

            serializer = FeedbackAnswerDetailSerializer(
                page if page is not None else answers_qs,
                many=True,
            )

            if page is not None:
                return paginator.get_paginated_response(
                    serializer.data
                )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error fetching feedback responses: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    # -----------------------------------
    # SUBMIT FEEDBACK
    # -----------------------------------
    @action(
        detail=False,
        methods=["post"],
        url_path="submit",
    )
    def submit_feedback(self, request: Request):
        try:
            serializer = SubmitFeedbackSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            answers = serializer.validated_data["answers"]

            with transaction.atomic():
                for answer in answers:
                    FeedbackAnswer.objects.create(
                        question=answer["question"],
                        option=answer.get("option"),
                        text=answer.get("text", "").strip(),
                    )

            return Response(
                {
                    "detail": "Feedback submitted successfully.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(
                f"Submit feedback: {e}",
                exc_info=True,
            )

            return Response(
                {
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # DELETE OPTION
    # -----------------------------------
    @action(
        detail=True,
        methods=["delete"],
        url_path="options/(?P<option_id>[^/.]+)",
    )
    def delete_option(
        self,
        request: Request,
        pk=None,
        option_id=None,
    ):
        try:
            question = Question.objects.filter(id=pk).first()

            if not question:
                return Response(
                    {"detail": "Question not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            option = Option.objects.filter(
                id=option_id,
                question=question,
            ).first()

            if not option:
                return Response(
                    {"detail": "Option not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if question.answers.exists():
                return Response(
                    {
                        "detail": (
                            "This option cannot be deleted because "
                            "feedback has already been submitted."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            option.delete()

            return Response(
                {"detail": "Option deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Delete feedback option {option_id}: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
    # -----------------------------------
    # DELETE QUESTION
    # -----------------------------------
    def destroy(self, request: Request, pk=None):
        try:
            question = (
                Question.objects
                .prefetch_related("options", "answers")
                .filter(id=pk)
                .first()
            )

            if not question:
                return Response(
                    {"detail": "Question not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if question.answers.exists():
                return Response(
                    {
                        "detail": (
                            "This question cannot be deleted because "
                            "feedback has already been submitted."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                # Explicitly delete options (CASCADE would also handle this)
                question.options.all().delete()

                question.delete()

            return Response(
                {"detail": "Question deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Delete feedback question {pk}: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    # -----------------------------------
    # CREATE QUESTION
    # -----------------------------------
    def create(self, request: Request):
        serializer = CreateQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            conference = Conference.objects.filter(
                conference_id=serializer.validated_data["conference_id"]
            ).first()

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            options = serializer.validated_data.get("options", [])
            question_type = serializer.validated_data["type"]

            if (
                question_type == QuestionTypeEnum.TEXT.value
                and len(options) > 0
            ):
                return Response(
                    {
                        "detail":
                        "Text questions cannot have options."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                question_type == QuestionTypeEnum.MULTIPLE_CHOICE.value
                and len(options) == 0
            ):
                return Response(
                    {
                        "detail":
                        "Multiple choice questions require at least one option."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                requested_position = serializer.validated_data["position"]

                while Question.objects.filter(
                    conference=conference,
                    position=requested_position,
                ).exists():
                    requested_position += 1

                question = Question.objects.create(
                    conference=conference,
                    question=serializer.validated_data["question"],
                    type=question_type,
                    is_required=serializer.validated_data["is_required"],
                    position=requested_position,
                )

                for item in options:
                    option_position = item["position"]

                    while Option.objects.filter(
                        question=question,
                        position=option_position,
                    ).exists():
                        option_position += 1

                    Option.objects.create(
                        question=question,
                        option=item["option"],
                        position=option_position,
                    )

            question.refresh_from_db()

            return Response(
                {
                    "detail": "Question created successfully.",
                    "question": QuestionSerializer(question).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(
                f"Create feedback question error: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


    # -----------------------------------
    # UPDATE QUESTION
    # -----------------------------------
    def update(self, request: Request, pk=None):
        serializer = UpdateQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            question = (
                Question.objects
                .prefetch_related("options")
                .filter(id=pk)
                .first()
            )

            if not question:
                return Response(
                    {"detail": "Question not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            with transaction.atomic():

                if "question" in serializer.validated_data:
                    question.question = serializer.validated_data["question"]

                if "type" in serializer.validated_data:
                    question.type = serializer.validated_data["type"]

                if "is_required" in serializer.validated_data:
                    question.is_required = serializer.validated_data["is_required"]

                if "position" in serializer.validated_data:
                    question.position = serializer.validated_data["position"]

                options = serializer.validated_data.get("options")

                if options is not None:

                    if (
                        question.type == QuestionTypeEnum.TEXT.value
                        and len(options) > 0
                    ):
                        return Response(
                            {
                                "detail":
                                "Text questions cannot have options."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    if (
                        question.type == QuestionTypeEnum.MULTIPLE_CHOICE.value
                        and len(options) == 0
                    ):
                        return Response(
                            {
                                "detail":
                                "Multiple choice questions require at least one option."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    question.options.all().delete()

                    for item in options:
                        Option.objects.create(
                            question=question,
                            option=item["option"],
                            position=item["position"],
                        )

                question.save()

            question.refresh_from_db()

            return Response(
                {
                    "detail": "Question updated successfully.",
                    "question": QuestionSerializer(question).data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Update feedback question {pk}: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # LIST QUESTIONS
    # -----------------------------------
    def list(self, request: Request):
        serializer = QuestionFilterQuerySerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        conference_id = serializer.validated_data["conference_id"]

        try:
            conference = Conference.objects.filter(
                conference_id=conference_id
            ).first()

            if not conference:
                return Response(
                    {"detail": "Conference not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            questions = (
                Question.objects
                .filter(conference=conference)
                .prefetch_related("options")
                .order_by("position")
            )

            paginator = PageNumberPagination()
            paginator.page_size_query_param = "page_size"

            page = paginator.paginate_queryset(
                questions,
                request,
            )

            serializer = QuestionSerializer(
                page if page is not None else questions,
                many=True,
            )

            if page is not None:
                return paginator.get_paginated_response(
                    serializer.data
                )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error fetching feedback questions: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------------------
    # RETRIEVE QUESTION
    # -----------------------------------
    def retrieve(self, request: Request, pk=None):
        try:
            question = (
                Question.objects
                .select_related("conference")
                .prefetch_related("options")
                .filter(id=pk)
                .first()
            )

            if not question:
                return Response(
                    {"detail": "Question not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                QuestionSerializer(question).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Retrieve feedback question {pk}: {e}",
                exc_info=True,
            )

            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )