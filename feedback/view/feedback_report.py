# import logging
# from typing import cast

# from django.http import HttpRequest
# from feedback.enums.question_type import QuestionTypeEnum
# from feedback.models import Question, FeedbackAnswer
# from rest_framework import viewsets, status, permissions
# from rest_framework.decorators import action
# from rest_framework.response import Response


# from feedback.serializers import QuestionReportSerializer
# from user.models import User

# logger = logging.getLogger(__name__)


# class FeedbackReportViewSet(viewsets.ViewSet):
#     permission_classes = [permissions.IsAuthenticated]

#     @action(detail=False, methods=["get"], url_path="conference-report")
#     def get_conference_report(self, request: HttpRequest):
#         conference_id = request.GET.get("conference_id")

#         if not conference_id:
#             return Response({"detail": "conference_id is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             questions = Question.objects.filter(conference_id=conference_id).prefetch_related("options", "answers")
#             report_data = []

#             for q in questions:
#                 if q.type == QuestionTypeEnum.MULTIPLE_CHOICE.value:
#                     option_counts = []
#                     for option in q.options.all():
#                         count = FeedbackAnswer.objects.filter(question=q, option=option).count()
#                         option_counts.append({
#                             "option_id": option.id,
#                             "option_text": option.option,
#                             "count": count
#                         })
#                     report_data.append({
#                         "question_id": q.id,
#                         "question_text": q.question,
#                         "type": q.type,
#                         "options": option_counts
#                     })

#                 elif q.type == QuestionTypeEnum.TEXT.value:
#                     answers = FeedbackAnswer.objects.filter(
#                         question=q,
#                         text__isnull=False
#                     ).exclude(text="").values("text", "submitted_at")
#                     report_data.append({
#                         "question_id": q.id,
#                         "question_text": q.question,
#                         "type": q.type,
#                         "answers": list(answers)
#                     })

#             serializer = QuestionReportSerializer(report_data, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception("Error generating feedback report")
#             return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
