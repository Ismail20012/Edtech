from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Sum, F, ExpressionWrapper, FloatField

class Student(models.Model):
    first_name_fr = models.CharField(max_length=100)
    last_name_fr = models.CharField(max_length=100)
    first_name_ar = models.CharField(max_length=100)
    last_name_ar = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=50, unique=True)

    class Meta:
        indexes = [
            GinIndex(name='student_first_fr_trgm', fields=['first_name_fr'], opclasses=['gin_trgm_ops']),
            GinIndex(name='student_last_fr_trgm', fields=['last_name_fr'], opclasses=['gin_trgm_ops']),
            GinIndex(name='student_first_ar_trgm', fields=['first_name_ar'], opclasses=['gin_trgm_ops']),
            GinIndex(name='student_last_ar_trgm', fields=['last_name_ar'], opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.first_name_fr} {self.last_name_fr} ({self.first_name_ar} {self.last_name_ar})"

class Subject(models.Model):
    name_fr = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    coefficient = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.name_fr} / {self.name_ar}"

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    value = models.FloatField()  # Out of 20
    term = models.IntegerField()  # 1, 2, or 3
    academic_year = models.CharField(max_length=9)  # e.g., "2025-2026"

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.value}"

class StudentTerm(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.IntegerField()
    academic_year = models.CharField(max_length=9)
    
    @property
    def moyenne_generale(self):
        grades = Grade.objects.filter(
            student=self.student,
            term=self.term,
            academic_year=self.academic_year
        ).annotate(
            weighted_grade=ExpressionWrapper(F('value') * F('subject__coefficient'), output_field=FloatField())
        )
        total_weighted = grades.aggregate(Sum('weighted_grade'))['weighted_grade__sum'] or 0
        total_coefficients = Subject.objects.filter(grade__in=grades).aggregate(Sum('coefficient'))['coefficient__sum'] or 1
        return total_weighted / total_coefficients

class TuitionPayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

class DraftGrade(models.Model):
    batch_id = models.CharField(max_length=100, null=True, blank=True)
    student_name_raw = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_raw = models.CharField(max_length=50)
    confidence_score = models.FloatField()
    matched_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
