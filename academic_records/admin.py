from django.contrib import admin
from .models import Score, RewardAndDiscipline, Evaluation

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'subject_name', 'score_value', 'exam_type', 'exam_date', 'academic_period')
    list_filter = ('exam_type', 'academic_period', 'subject', 'student__current_class')
    search_fields = (
        'student__user__username',
        'student__user__first_name',
        'student__user__last_name',
        'subject__name',
        'exam_type'
    )
    # Thay đổi ở đây:
    raw_id_fields = ('student',) # Sử dụng raw_id_fields cho student
    autocomplete_fields = ['subject'] # Giữ autocomplete cho subject nếu SubjectAdmin có search_fields

    def student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student.user.get_full_name() else obj.student.user.username
    student_name.short_description = 'Học sinh'
    student_name.admin_order_field = 'student__user__last_name' # Cho phép sắp xếp theo tên học sinh

    def subject_name(self, obj):
        return obj.subject.name
    subject_name.short_description = 'Môn học'
    subject_name.admin_order_field = 'subject__name' # Cho phép sắp xếp theo tên môn học


@admin.register(RewardAndDiscipline)
class RewardAndDisciplineAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'record_type', 'reason_short', 'date_issued', 'issued_by_username')
    list_filter = ('record_type', 'date_issued', 'student__current_class')
    search_fields = (
        'student__user__username',
        'student__user__first_name',
        'student__user__last_name',
        'reason',
        'issued_by__username'
    )
    # Thay đổi ở đây:
    raw_id_fields = ('student',) # Sử dụng raw_id_fields cho student
    autocomplete_fields = ['issued_by'] # Giữ autocomplete cho issued_by
    date_hierarchy = 'date_issued'

    def student_name(self, obj):
        # ... (phần còn lại của lớp giữ nguyên) ...
        return obj.student.user.get_full_name() if obj.student.user.get_full_name() else obj.student.user.username
    student_name.short_description = 'Học sinh'
    student_name.admin_order_field = 'student__user__last_name'

    def issued_by_username(self, obj):
        return obj.issued_by.username if obj.issued_by else '-'
    issued_by_username.short_description = 'Người Quyết định'
    issued_by_username.admin_order_field = 'issued_by__username'

    def reason_short(self, obj):
        return obj.reason[:75] + '...' if len(obj.reason) > 75 else obj.reason
    reason_short.short_description = 'Lý do/Nội dung'


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'evaluation_type', 'evaluator_username', 'subject_name_optional', 'evaluation_date')
    list_filter = ('evaluation_type', 'evaluation_date', 'evaluator', 'subject', 'student__current_class')
    search_fields = (
        'student__user__username',
        'student__user__first_name',
        'student__user__last_name',
        'evaluator__username',
        'subject__name',
        'content'
    )

    raw_id_fields = ('student', 'subject') 
    autocomplete_fields = ['evaluator'] # Giữ autocomplete cho evaluator
    date_hierarchy = 'evaluation_date'


    def student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student.user.get_full_name() else obj.student.user.username
    student_name.short_description = 'Học sinh'

    def evaluator_username(self, obj):
        return obj.evaluator.username if obj.evaluator else '-'
    evaluator_username.short_description = 'Người đánh giá'

    def subject_name_optional(self, obj):
        return obj.subject.name if obj.subject else '-'
    subject_name_optional.short_description = 'Môn học (nếu có)'