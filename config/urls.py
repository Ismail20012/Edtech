from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.admin_urls if hasattr(admin.site, 'admin_urls') else admin.site.urls),
    path('', views.upload_grades, name='home'),
    path('upload/', views.upload_grades, name='upload_grades'),
    path('check_status/<str:batch_id>/', views.check_ocr_status, name='check_ocr_status'),
    path('confirm_draft/<int:draft_id>/', views.confirm_draft, name='confirm_draft'),
]
