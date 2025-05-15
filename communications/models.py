from django.db import models
from django.conf import settings 
from django.utils import timezone
# Create your models here.
class Notification(models.Model):
    # ERD: notice_id (PK - Django tự tạo)
    # ERD: title, content, created_time, send_by, status

    STATUS_CHOICES = [
        ('DRAFT', 'Bản nháp'),
        ('SENT', 'Đã gửi'),
        ('READ', 'Đã xem'), 
        ('ARCHIVED', 'Đã lưu trữ'),
    ]

    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Tham chiếu an toàn đến User model
        on_delete=models.SET_NULL, # Nếu người gửi bị xóa, thông báo vẫn còn nhưng không rõ người gửi
        null=True,
        blank=True, 
        related_name='sent_notifications',
        verbose_name="Người gửi"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Trạng thái")
    publish_time = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian gửi dự kiến") # Thời điểm thông báo sẽ được gửi đi

    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_notifications', # Từ User, có thể xem các thông báo họ nhận
        blank=True,
        verbose_name="Người nhận cụ thể"
    )

    # Trường hợp gửi đến các vai trò:
    target_roles = models.ManyToManyField(
        'accounts.Role', # Tham chiếu đến Role model trong app 'accounts'
        related_name='role_notifications', # Từ Role, có thể xem các thông báo gửi cho vai trò đó
        blank=True,
        verbose_name="Gửi đến Vai trò"
    )

    # Trường hợp gửi đến các lớp học:
    target_classes = models.ManyToManyField(
        'school_data.Class', # Tham chiếu đến Class model trong app 'school_data'
        related_name='class_notifications', # Từ Class, có thể xem các thông báo gửi cho lớp đó
        blank=True,
        verbose_name="Gửi đến Lớp học"
    )

    is_published = models.BooleanField(default=False, verbose_name="Đã phát hành")


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Các Thông báo"
        ordering = ['-created_time'] 

class Conversation(models.Model):
    CONVERSATION_TYPE_CHOICES = [
        ('DIRECT', 'Trò chuyện trực tiếp (1-1)'),
        ('GROUP', 'Trò chuyện nhóm'),
    ]

    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tiêu đề cuộc hội thoại (cho nhóm)")
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name="Thành viên tham gia"
    )
    conversation_type = models.CharField(
        max_length=10,
        choices=CONVERSATION_TYPE_CHOICES,
        default='DIRECT',
        verbose_name="Loại cuộc hội thoại"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối") # Thời gian của tin nhắn cuối cùng

    def __str__(self):
        if self.conversation_type == 'GROUP' and self.title:
            return self.title
        elif self.conversation_type == 'DIRECT':

            participant_names = ", ".join([user.username for user in self.participants.all()[:2]]) # Lấy 2 người đầu tiên
            return f"Trò chuyện giữa: {participant_names}"
        return f"Cuộc hội thoại ID: {self.id}"

    class Meta:
        verbose_name = "Cuộc hội thoại"
        verbose_name_plural = "Các Cuộc hội thoại"
        ordering = ['-updated_at'] # Sắp xếp theo thời gian cập nhật mới nhất

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE, 
        related_name='messages', 
        verbose_name="Thuộc cuộc hội thoại"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_messages_in_conversation',
        verbose_name="Người gửi"
    )
    content = models.TextField(verbose_name="Nội dung tin nhắn")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian gửi")


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        if self.conversation:
            self.conversation.updated_at = timezone.now() 
            self.conversation.save(update_fields=['updated_at'])

    def __str__(self):
        return f"Tin nhắn từ {self.sender.username if self.sender else 'Hệ thống'} lúc {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Tin nhắn"
        verbose_name_plural = "Các Tin nhắn"
        ordering = ['sent_at'] # Sắp xếp tin nhắn theo thời gian gửi


from django.db import models
from django.conf import settings 
from django.utils import timezone 

class RequestForm(models.Model):
    FORM_TYPE_CHOICES = [
        ('LEAVE_APPLICATION', 'Đơn xin nghỉ học'),
        ('GRADE_APPEAL', 'Đơn phúc khảo điểm'),
        ('GENERAL_REQUEST', 'Kiến nghị/Đề xuất chung'),
        ('FEEDBACK', 'Góp ý'),
    ]

    STATUS_CHOICES = [
        ('SUBMITTED', 'Mới gửi'),
        ('PROCESSING', 'Đang xử lý'),
        ('RESOLVED', 'Đã giải quyết'),
        ('REJECTED', 'Đã từ chối'),
        ('CLOSED', 'Đã đóng'),
    ]

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_forms',
        verbose_name="Người gửi"
    )
    related_student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_request_forms',
        verbose_name="Học sinh liên quan (nếu có)"
    )
    form_type = models.CharField(max_length=50, choices=FORM_TYPE_CHOICES, verbose_name="Loại đơn")
    title = models.CharField(max_length=255, verbose_name="Tiêu đề đơn/kiến nghị")
    content = models.TextField(verbose_name="Nội dung chi tiết")
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name="Ngày gửi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED', verbose_name="Trạng thái")

    assigned_department = models.ForeignKey(
        'school_data.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Cho phép không chọn phòng ban (nếu gửi cho giáo viên)
        related_name='assigned_request_forms',
        verbose_name="Phòng Ban xử lý"
    )


    assigned_teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_request_forms', # Các đơn mà giáo viên này nhận/xử lý
        blank=True, # Cho phép không chọn giáo viên (nếu gửi cho phòng ban)
        limit_choices_to={'role__name': 'TEACHER'}, # Chỉ những User có vai trò là Giáo viên
        verbose_name="Giáo viên xử lý/nhận đơn"
    )


    response_content = models.TextField(blank=True, null=True, verbose_name="Nội dung phản hồi từ nhà trường")
    response_date = models.DateTimeField(null=True, blank=True, verbose_name="Ngày phản hồi")
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responded_request_forms', # Đổi tên related_name này để tránh xung đột với assigned_teachers
        limit_choices_to={'is_staff': True},
        verbose_name="Người phản hồi"
    )

    def __str__(self):
        return f"{self.get_form_type_display()} từ {self.submitted_by.username} - {self.title}"

    class Meta:
        verbose_name = "Đơn từ/Kiến nghị"
        verbose_name_plural = "Các Đơn từ/Kiến nghị"
        ordering = ['-submission_date']