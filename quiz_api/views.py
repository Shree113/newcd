import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
import json
from django.utils.decorators import method_decorator
from .models import Student, Question, StudentAnswer
from .serializers import StudentSerializer, QuestionSerializer, StudentAnswerSerializer

logger = logging.getLogger(__name__)


@csrf_exempt  # ✅ Disable CSRF for this API (ONLY if needed)
def create_student(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # ✅ Ensure JSON is parsed
            student = Student.objects.create(
                name=data["name"],
                email=data["email"],
                department=data["department"],
                college=data["college"],
                year=data["year"]
            )
            return JsonResponse({"id": student.id, "message": "Student created successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

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


# Add this import at the top with your other imports
import subprocess
import tempfile
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json

# Add this new view function
@api_view(['POST'])
def compile_code(request):
    """
    Compile and run code in various languages
    """
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(suffix=get_file_extension(language), delete=False) as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name
        
        # Compile and run the code
        result = run_code(temp_file_path, language)
        
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass
        
        return Response({'output': result})
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_file_extension(language):
    """Get the appropriate file extension for the language"""
    extensions = {
        'python': '.py',
        'c': '.c'
    }
    return extensions.get(language, '.txt')

def run_code(file_path, language):
    try:
        if language == 'python':
            # Run Python code
            result = subprocess.run(['python', file_path], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=10)
            
        elif language == 'c':
            # Check if gcc is installed
            try:
                subprocess.run(['gcc', '--version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                return "Error: C compiler (gcc) is not installed on the server. Please try Python code instead."
                
            # Compile C code
            output_path = file_path.replace('.c', '.exe')
            compile_result = subprocess.run(['gcc', file_path, '-o', output_path], 
                                           capture_output=True, 
                                           text=True, 
                                           timeout=10)
            
            if compile_result.returncode != 0:
                return f"Compilation Error:\n{compile_result.stderr}"
            
            # Run the compiled executable
            result = subprocess.run([output_path], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=10)
            
            # Clean up the executable
            try:
                os.unlink(output_path)
            except:
                pass
        else:
            return "Unsupported language"
        
        # Combine stdout and stderr
        output = result.stdout
        if result.returncode != 0:
            output += f"\nError (exit code {result.returncode}):\n{result.stderr}"
        
        return output
    
    except subprocess.TimeoutExpired:
        return "Execution timed out (limit: 30 seconds)"
    except Exception as e:
        return f"Execution error: {str(e)}"
