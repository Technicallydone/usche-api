# import logging

# from django.http import HttpRequest
# from feedback.models import FeedbackAnswer
# from feedback.models import Question
# from feedback.serializers import SingleAnswerSerializer, QuestionSerializer
# from rest_framework import viewsets, permissions, status
# from rest_framework.decorators import action
# from rest_framework.response import Response

# logger = logging.getLogger(__name__)

# class ConferenceQuestionViewSet(viewsets.ViewSet):
#     permission_classes = [permissions.AllowAny]

#     @action(detail=False, methods=["get"])
#     def get_questions_by_conference(self, request: HttpRequest):
#         conference_id = request.GET.get('conference_id')
        
#         if conference_id is None:
#             return Response(data={"detail": "Conference id not provided"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             questions = Question.objects.filter(conference_id=conference_id).prefetch_related('options')
#             serializer = QuestionSerializer(questions, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.error(f"Error fetching questions: {e}")
#             return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     @action(detail=False, methods=["post"])
#     def submit_feedback(self, request: HttpRequest):
#         try:
#             answers = request.data.get("answers", [])
#             errors = []

#             for ans in answers:
#                 serializer = SingleAnswerSerializer(data=ans)
#                 if serializer.is_valid():
#                     validated = serializer.validated_data
#                     FeedbackAnswer.objects.create(
#                         question=validated["question"],
#                         option=validated.get("option"),
#                         text=validated["answer"]
#                     )
#                 else:
#                     errors.append(serializer.errors)

#             if errors:
#                 return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

#             return Response({"detail": "Feedback submitted successfully."}, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             logger.error(f"Error while submitting feedback: {str(e)}")
#             return Response(
#                 {"detail": "An error occurred while submitting feedback."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
