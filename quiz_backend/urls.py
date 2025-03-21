"""
URL configuration for codeverse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from quiz_api.views import complete_quiz, superuser_login
from django.contrib.auth.decorators import login_required
from quiz_api import views
from .views import compile_code


def home(request):
    return HttpResponse("Welcome to the Quiz App!")

urlpatterns = [
    path('admin/', admin.site.urls),  # ✅ Ensure this is included

    path('admin/', login_required(admin.site.admin_view(admin.site.index))),
    # Our API endpoints:
    path('api/student/', views.create_student, name='create_student'),
    path('api/questions/', views.get_questions, name='get_questions'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
    path('api/leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/delete-student/<int:pk>/', views.delete_student, name='delete_student'),
    path('api/login/', superuser_login, name='superuser_login'),  # ✅ Superuser login
    path('api/complete-quiz/', complete_quiz, name='complete_quiz'), 
    path('compile/', compile_code, name='compile_code'),  

]
