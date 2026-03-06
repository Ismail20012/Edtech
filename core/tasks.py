from celery import shared_task
from ocr_service.processor import process_grade_sheet
from core.models import DraftGrade, Subject, Student
import os

@shared_task
def process_ocr_task(image_path, subject_id, batch_id):
    results = process_grade_sheet(image_path, subject_id)
    subject = Subject.objects.get(id=subject_id)
    
    # Save results to DraftGrade
    for res in results:
        DraftGrade.objects.create(
            batch_id=batch_id,
            student_name_raw=res['student_name_raw'],
            subject=subject,
            grade_raw=res['grade'],
            confidence_score=res['confidence_score'],
            matched_student_id=res['student_id'],
            is_confirmed=False
        )
    
    # Optionally delete image or keep for verification
    # os.remove(image_path)
    return f"Processed {len(results)} rows"
