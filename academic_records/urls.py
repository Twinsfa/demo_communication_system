from django.urls import path
from . import views

app_name = 'academic_records'

urlpatterns = [
    # ... (các URL cho scores, rewards-discipline, add/edit evaluation, view_evaluations đã có) ...
    path('scores/', views.view_scores, name='view_scores'),
    path('enter-scores/', views.enter_scores, name='enter_scores'),
    path('teacher/class-scores/', views.manage_scores_dashboard, name='teacher_view_class_scores'),
    
    path('rewards-discipline/', views.view_reward_discipline, name='view_reward_discipline'),
    path('teacher/class-rewards-discipline/', views.teacher_view_class_rewards_discipline, name='teacher_view_class_rewards_discipline'),
    path('rewards-discipline/add/', views.manage_reward_discipline_record, name='add_reward_discipline'),
    path('rewards-discipline/<int:pk>/edit/', views.manage_reward_discipline_record, name='edit_reward_discipline'),
    path('school-wide/rewards-discipline/', views.school_wide_reward_discipline_list, name='school_wide_reward_discipline_list'),

    path('evaluations/add/', views.create_edit_evaluation, name='add_evaluation'), 
    path('evaluations/<int:pk>/edit/', views.create_edit_evaluation, name='edit_evaluation'), 
    path('evaluations/view/', views.view_evaluations, name='view_evaluations'),

    # URL MỚI CHO GIÁO VIÊN XEM ĐÁNH GIÁ CỦA MÌNH
    path('teacher/my-evaluations/', views.teacher_my_evaluations, name='teacher_my_evaluations'),
]
