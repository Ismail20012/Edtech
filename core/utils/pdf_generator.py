from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from core.models import Student, Grade, Subject, StudentTerm

def generate_transcript_pdf(student_id, term, academic_year):
    student = Student.objects.get(id=student_id)
    grades = Grade.objects.filter(student=student, term=term, academic_year=academic_year).select_related('subject')
    
    # Calculate Moyenne
    weighted_sum = 0
    total_coeffs = 0
    rows = []
    
    for grade in grades:
        definitive = grade.value * grade.subject.coefficient
        weighted_sum += definitive
        total_coeffs += grade.subject.coefficient
        rows.append({
            'subject_fr': grade.subject.name_fr,
            'subject_ar': grade.subject.name_ar,
            'note': grade.value,
            'coeff': grade.subject.coefficient,
            'definitive': definitive
        })
    
    moyenne = weighted_sum / total_coeffs if total_coeffs > 0 else 0
    
    # Simple Rank calculation (optimized for this student)
    # In a real system, you'd calculate all moyennes and then find the rank.
    all_students_in_term = StudentTerm.objects.filter(term=term, academic_year=academic_year)
    # Mock rank for now as it requires full class data
    rank = "1 / " + str(all_students_in_term.count()) 

    context = {
        'student': student,
        'rows': rows,
        'moyenne': moyenne,
        'rank': rank,
        'term': term,
        'academic_year': academic_year
    }
    
    html_string = render_to_string('core/pdf/transcript.html', context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    return pdf_file
