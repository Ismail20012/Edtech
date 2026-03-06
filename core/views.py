import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Student, Subject, DraftGrade, Grade
from .tasks import process_ocr_task
from django.views.decorators.csrf import csrf_exempt

def upload_grades(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file_obj = request.FILES['file']
        subject_id = request.POST.get('subject_id')
        batch_id = str(uuid.uuid4())
        
        # Save file to media root
        file_path = default_storage.save(f'ocr_uploads/{file_obj.name}', file_obj)
        full_path = default_storage.path(file_path)
        
        # Trigger Celery task
        process_ocr_task.delay(full_path, subject_id, batch_id)
        
        return render(request, 'core/partials/loading.html', {'batch_id': batch_id})
    
    subjects = Subject.objects.all()
    return render(request, 'core/upload.html', {'subjects': subjects})

def check_ocr_status(request, batch_id):
    drafts = DraftGrade.objects.filter(batch_id=batch_id, is_confirmed=False)
    if drafts.exists():
        return render(request, 'core/partials/draft_table.html', {'drafts': drafts, 'batch_id': batch_id})
    
    # Still processing or none found
    return HttpResponse('<div hx-get="/check_status/' + batch_id + '/" hx-trigger="every 2s" hx-swap="outerHTML"><span class="animate-spin mr-2">🔄</span> Processing grade sheet...</div>')

@csrf_exempt
def confirm_draft(request, draft_id):
    if request.method == 'POST':
        draft = get_object_or_404(DraftGrade, id=draft_id)
        # Finalize the grade
        grade_val = request.POST.get('grade')
        student_id = request.POST.get('student_id')
        
        if student_id:
            Grade.objects.create(
                student_id=student_id,
                subject=draft.subject,
                value=float(grade_val),
                term=1, # Default or get from request
                academic_year="2025-2026"
            )
            draft.is_confirmed = True
            draft.save()
            return HttpResponse(f'<span class="text-green-500">Confirmed</span>')
    
    return HttpResponse('Error', status=400)
