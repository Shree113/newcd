import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

from .models import Student, Question, StudentAnswer
from .serializers import StudentSerializer, QuestionSerializer, StudentAnswerSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
def create_student(request):
    """
    Create a new student entry.
    """
    serializer = StudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def superuser_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_superuser:  # ✅ Allow only superusers
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized as an admin"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# quiz/views.py
@api_view(['DELETE'])
def delete_student(request, pk):
    try:
        student = Student.objects.get(pk=pk)
        student.delete()
        return Response({'message': 'Student deleted'}, status=200)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)


@api_view(['GET'])
def get_questions(request):
    """
    Retrieve all quiz questions.
    """
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def submit_answer(request):
    """
    Submit an answer for a question.
    """
    student_id = request.data.get('student_id')
    question_id = request.data.get('question_id')
    chosen_option = request.data.get('chosen_option')

    student = get_object_or_404(Student, id=student_id)
    question = get_object_or_404(Question, id=question_id)

    # Check correctness
    is_correct = (chosen_option.upper() == question.correct_option.upper())

    # Create or update the StudentAnswer
    answer, created = StudentAnswer.objects.update_or_create(
        student=student,
        question=question,
        defaults={'chosen_option': chosen_option, 'is_correct': is_correct}
    )

    # If correct, add 5 points
    if is_correct:
        student.total_score += 5
        student.save()

    return Response({
        'is_correct': is_correct,
        'current_score': student.total_score
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def leaderboard(request):
    """
    Return students ordered by total_score descending.
    """
    students = Student.objects.all().order_by('-total_score')
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def complete_quiz(request):
    # Extract data from the request
    student_id = request.data.get('student_id')
    score = request.data.get('score')
    
    if not student_id or score is None:
        logger.error("Missing student_id or score in the request.")
        return Response({"error": "Missing student_id or score"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Retrieve the student or return an error if not found
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        logger.error(f"Student with id {student_id} not found.")
        return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Update the student's total score
    student.total_score = score
    student.save()

    # Compose the email
    subject = "Your Quiz Results"
    message = f"Hello {student.name},\n\nThank you for completing the quiz! Your final score is {score}."
    recipient_list = [student.email]

    # Send the email
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
    except Exception as e:
        logger.error("Email could not be sent: " + str(e))
        return Response({"error": "Email could not be sent", "details": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Quiz completed and email sent!"}, status=status.HTTP_200_OK)
