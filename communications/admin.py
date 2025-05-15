from django.contrib import admin
from .models import Notification, Conversation, Message, RequestForm # Thêm RequestForm vào import

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'sent_by', 'status', 'created_time', 'publish_time', 'is_published')
    list_filter = ('status', 'is_published', 'created_time', 'publish_time', 'sent_by')
    search_fields = ('title', 'content', 'sent_by__username') 
    
    filter_horizontal = ('target_users', 'target_roles', 'target_classes') 

    fieldsets = (
        (None, { 
            'fields': ('title', 'content', 'sent_by', 'status', 'publish_time', 'is_published')
        }),
        ('Đối tượng nhận', { 
            'classes': ('collapse',), 
            'fields': ('target_users', 'target_roles', 'target_classes') 
        }),
    )


class MessageInline(admin.TabularInline):
    model = Message
    extra = 1 
    fields = ('sender', 'content', 'sent_at') 
    readonly_fields = ('sent_at',) 


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'conversation_type', 'created_at', 'updated_at', 'display_participants')
    list_filter = ('conversation_type', 'created_at', 'updated_at')
    search_fields = ('title', 'participants__username') # Tìm theo username của người tham gia
    filter_horizontal = ('participants',) # Widget tốt cho ManyToManyField participants
    inlines = [MessageInline] # Hiển thị Messages như một phần của Conversation

    def display_participants(self, obj):
        # Hiển thị tối đa 3 người tham gia, còn lại là "..."
        participants = obj.participants.all()
        if participants.count() > 3:
            return ", ".join([user.username for user in participants[:3]]) + ", ..."
        return ", ".join([user.username for user in participants])
    display_participants.short_description = "Thành viên" # Đặt tên cột


@admin.register(RequestForm)
class RequestFormAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'submitted_by',
        'form_type',
        'status',
        'submission_date',
        'assigned_department',
        'display_assigned_teachers', # Thêm để hiển thị giáo viên
        'response_date'
    )
    list_filter = ('status', 'form_type', 'submission_date', 'assigned_department', 'assigned_teachers') # Thêm assigned_teachers
    search_fields = (
        'title',
        'content',
        'submitted_by__username',
        'related_student__user__username',
        'assigned_teachers__username' # Tìm theo username của giáo viên được gán
    )
    fieldsets = (
        ('Thông tin Đơn', {
            'fields': ('title', 'form_type', 'submitted_by', 'related_student', 'content')
        }),
        ('Đối tượng Xử lý', { # Đổi tên nhóm hoặc thêm nhóm mới
            'fields': ('assigned_department', 'assigned_teachers') # Thêm assigned_teachers
        }),
        ('Xử lý và Trạng thái', {
            'fields': ('status',)
        }),
        ('Phản hồi từ Nhà trường', {
            'classes': ('collapse',),
            'fields': ('response_content', 'responded_by', 'response_date')
        }),
    )
    readonly_fields = ('submission_date',)
    autocomplete_fields = ['submitted_by', 'related_student', 'assigned_department', 'responded_by'] # Giữ nguyên
    filter_horizontal = ('assigned_teachers',) 

    def display_assigned_teachers(self, obj):
        return ", ".join([teacher.username for teacher in obj.assigned_teachers.all()])
    display_assigned_teachers.short_description = 'Giáo viên nhận'