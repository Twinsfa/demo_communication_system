from django.urls import path
from . import views # Chúng ta sẽ tạo views.py sau

app_name = 'communications' # Đặt namespace cho app này

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('notifications/', views.notification_list, name='notification_list'), 
    path('submit-request/', views.submit_request_form, name='submit_request_form'), 
    path('my-requests/', views.my_submitted_requests, name='my_submitted_requests'), 
    path('department-requests/', views.department_request_list, name='department_request_list'), 
    path('department-requests/<int:pk>/respond/', views.department_request_detail_respond, name='department_respond_request'), 
    path('teacher-requests/', views.teacher_request_list, name='teacher_request_list'),
    path('teacher-requests/<int:pk>/respond/', views.teacher_request_detail_respond, name='teacher_respond_request'),
    path('messages/', views.conversation_list, name='conversation_list'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'), 
    path('messages/new/', views.start_new_conversation, name='start_new_conversation'),
    path('notifications/create/', views.create_notification, name='create_notification'),


]