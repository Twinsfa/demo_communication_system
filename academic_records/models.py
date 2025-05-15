from django.db import models
from django.conf import settings 

class Score(models.Model):
    # ERD: grade_id (PK), score, exam_type, exam_date
    # Liên kết N:M với STUDENT và SUBJECT 
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE, 
        related_name='scores',
        verbose_name="Học sinh"
    )
    subject = models.ForeignKey(
        'school_data.Subject',
        on_delete=models.CASCADE, 
        related_name='scores',
        verbose_name="Môn học"
    )
    score_value = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Điểm số") # Ví dụ: 9.75
    EXAM_TYPE_CHOICES = [
        ('MID_TERM_1', 'Giữa Học kỳ 1'),
        ('END_TERM_1', 'Cuối Học kỳ 1'),
        ('MID_TERM_2', 'Giữa Học kỳ 2'),
        ('END_TERM_2', 'Cuối Học kỳ 2'),
        ('FINAL_EXAM', 'Thi Tốt nghiệp (Nếu có)'),
        ('ORAL_TEST', 'Kiểm tra miệng'),
        ('15_MIN_TEST', 'Kiểm tra 15 phút'),
        ('45_MIN_TEST', 'Kiểm tra 1 tiết (45 phút)'),
        # Thêm các loại khác nếu cần
    ]
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, verbose_name="Loại kỳ thi/kiểm tra")
    exam_date = models.DateField(verbose_name="Ngày thi/kiểm tra")
    academic_period = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kỳ học/Năm học (VD: HK1 2024-2025)")
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú (nếu có)")

    def __str__(self):
        return f"{self.student.user.username} - {self.subject.name}: {self.score_value} ({self.get_exam_type_display()})"

    class Meta:
        verbose_name = "Điểm số"
        verbose_name_plural = "Các Điểm số"
        unique_together = ('student', 'subject', 'exam_type', 'exam_date', 'academic_period') # Đảm bảo không nhập trùng điểm
        ordering = ['-exam_date', 'subject']

class RewardAndDiscipline(models.Model):
    # ERD: reward_id (PK), type (khen thưởng/kỷ luật), date, content
    # Liên kết 1:N từ STUDENT 
    RECORD_TYPE_CHOICES = [
        ('REWARD', 'Khen thưởng'),
        ('DISCIPLINE', 'Kỷ luật'),
    ]
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='reward_discipline_records',
        verbose_name="Học sinh"
    )
    record_type = models.CharField(max_length=10, choices=RECORD_TYPE_CHOICES, verbose_name="Loại (Khen thưởng/Kỷ luật)")
    date_issued = models.DateField(verbose_name="Ngày quyết định")
    reason = models.TextField(verbose_name="Nội dung/Lý do")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_rewards_disciplines',
        limit_choices_to={'is_staff': True}, # Chỉ staff (giáo viên, admin) mới có thể ra quyết định
        verbose_name="Người ra quyết định"
    )

    def __str__(self):
        return f"{self.get_record_type_display()} cho {self.student.user.username} - {self.reason[:50]}..."

    class Meta:
        verbose_name = "Khen thưởng/Kỷ luật"
        verbose_name_plural = "Các mục Khen thưởng/Kỷ luật"
        ordering = ['-date_issued']

class Evaluation(models.Model):
    # ERD: evaluate_id (PK), evaluation_date, content
    # Liên kết N:1 từ STUDENT và 1:N từ TEACHER
    EVALUATION_TYPE_CHOICES = [
        ('CONDUCT', 'Đánh giá Hạnh kiểm'),
        ('SUBJECT_REVIEW', 'Nhận xét Môn học'),
        ('TERM_REVIEW', 'Đánh giá Cuối kỳ/Năm'),
        # Thêm các loại khác nếu cần
    ]
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Học sinh được đánh giá"
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Người đánh giá (thường là giáo viên)
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Có thể là đánh giá từ hệ thống hoặc ban giám hiệu
        related_name='given_evaluations',
        limit_choices_to={'role__name__in': ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN']}, # Giới hạn người đánh giá
        verbose_name="Người đánh giá"
    )
    # Nếu nhận xét môn học cụ thể
    subject = models.ForeignKey(
        'school_data.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Có thể là đánh giá chung, không phải cho môn cụ thể
        related_name='subject_evaluations',
        verbose_name="Môn học (nếu có)"
    )
    evaluation_type = models.CharField(max_length=30, choices=EVALUATION_TYPE_CHOICES, verbose_name="Loại đánh giá")
    evaluation_date = models.DateField(verbose_name="Ngày đánh giá")
    content = models.TextField(verbose_name="Nội dung đánh giá/nhận xét")

    def __str__(self):
        evaluator_name = self.evaluator.username if self.evaluator else "Hệ thống"
        return f"Đánh giá cho {self.student.user.username} bởi {evaluator_name} ({self.get_evaluation_type_display()})"

    class Meta:
        verbose_name = "Đánh giá/Nhận xét"
        verbose_name_plural = "Các Đánh giá/Nhận xét"
        ordering = ['-evaluation_date']