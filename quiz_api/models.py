from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    college = models.CharField(max_length=100)
    year = models.CharField(max_length=20)  # e.g. "1st Year", "2nd Year"

    total_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Question(models.Model):
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1)  # 'A', 'B', 'C', or 'D'

    def __str__(self):
        return self.text


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    chosen_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.question}"


class Leaderboard(Student):
    """
    A proxy model that references the same data as Student
    but is displayed as 'Leaderboard' in the Django admin.
    """
    class Meta:
        proxy = True               # <--- Tells Django it's a proxy of Student
        verbose_name = "Leaderboard"
        verbose_name_plural = "Leaderboard"
        ordering = ["-total_score"]  # <--- Sort by total_score descending
