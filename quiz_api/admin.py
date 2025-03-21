from django.contrib import admin
from .models import Student, Question, StudentAnswer, Leaderboard

# Register your models here.

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'total_score')
    ordering = ('-total_score',)
    search_fields = ('name', 'email')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'total_score')
    ordering = ('-total_score',)

    # Optional: make fields read-only so no one changes them in the Leaderboard view
    readonly_fields = ('id','name', 'email', 'department', 'college', 'year', 'total_score')

    # Optional: disable add/delete in Leaderboard view
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'correct_option')
    fieldsets = (
        ('General', {
            'fields': ('text', 'code_snippet')
        }),
        ('Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_option')
        }),
    )


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'chosen_option', 'is_correct')
