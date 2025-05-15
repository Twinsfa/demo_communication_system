from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Max, Count
from django.contrib.auth import get_user_model

from school_data.models import Class as SchoolClass # Import đúng model lớp học
from .forms import RequestFormSubmissionForm, RequestFormResponseForm, MessageForm, StartConversationForm, TeacherNotificationForm, DepartmentNotificationForm # Các form từ app này
from .models import Notification, RequestForm, Conversation, Message # Import lại các model cần thiết

@login_required
def notification_list(request):
    user = request.user
    direct_q = Q(target_users=user)
    role_q = Q()
    if hasattr(user, 'role') and user.role:
        role_q = Q(target_roles=user.role)
    class_q = Q()
    if hasattr(user, 'student_profile') and user.student_profile and hasattr(user.student_profile, 'current_class') and user.student_profile.current_class:
        class_q = Q(target_classes=user.student_profile.current_class)
    
    final_q = direct_q | role_q | class_q
    notifications = Notification.objects.filter(final_q, is_published=True, status='SENT').distinct().order_by('-publish_time', '-created_time')

    read_notification_ids = set() # TODO: Nếu có model NotificationRead, lấy id các notification user đã đọc
    notifications_created_by_me = None
    if (hasattr(user, 'role') and user.role and user.role.name == 'TEACHER') or (user.is_staff and hasattr(user, 'department') and user.department):
        notifications_created_by_me = Notification.objects.filter(sent_by=user).order_by('-publish_time', '-created_time')
    context = {
        'notifications': notifications,
        'page_title': 'Danh sách Thông báo',
        'read_notification_ids': read_notification_ids,
        'notifications_created_by_me': notifications_created_by_me,
    }
    return render(request, 'communications/notification_list.html', context)

@login_required
def submit_request_form(request):
    if request.method == 'POST':
        form = RequestFormSubmissionForm(request.POST, user=request.user)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.submitted_by = request.user
            
            # Xử lý related_student
            if 'related_student' in form.cleaned_data and form.cleaned_data['related_student']:
                new_request.related_student = form.cleaned_data['related_student']
            
            new_request.save()
            form.save_m2m()

            messages.success(request, 'Đơn của bạn đã được gửi thành công!')
            return redirect('communications:my_submitted_requests')
    else:
        form = RequestFormSubmissionForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Gửi Đơn từ / Kiến nghị'
    }
    return render(request, 'communications/submit_request_form.html', context)

@login_required
def my_submitted_requests(request):
    user_requests = RequestForm.objects.filter(submitted_by=request.user).order_by('-submission_date')
    context = {
        'user_requests': user_requests,
        'page_title': 'Đơn từ/Kiến nghị đã gửi'
    }
    return render(request, 'communications/my_submitted_requests.html', context)

@login_required
def department_request_list(request):
    user = request.user
    if not (user.is_staff and hasattr(user, 'department') and user.department):
        raise PermissionDenied("Bạn không có quyền truy cập trang này hoặc chưa được gán vào phòng ban.")

    department_requests = RequestForm.objects.filter(
        assigned_department=user.department
    ).order_by('submission_date')

    context = {
        'department_requests': department_requests,
        'page_title': f'Đơn từ/Kiến nghị cho {user.department.name}',
        'department_name': user.department.name
    }
    return render(request, 'communications/department_request_list.html', context)

@login_required
def department_request_detail_respond(request, pk):
    user = request.user
    if not (user.is_staff and hasattr(user, 'department') and user.department):
        raise PermissionDenied("Bạn không có quyền truy cập hoặc xử lý đơn này.")

    request_form_instance = get_object_or_404(
        RequestForm,
        pk=pk,
        assigned_department=user.department
    )

    if request.method == 'POST':
        response_form = RequestFormResponseForm(request.POST, instance=request_form_instance)
        if response_form.is_valid():
            updated_request_form = response_form.save(commit=False)
            updated_request_form.responded_by = user
            updated_request_form.response_date = timezone.now()
            updated_request_form.save() # Lưu các thay đổi vào instance

            # GỬI THÔNG BÁO CHO PHỤ HUYNH
            parent_user = updated_request_form.submitted_by
            student = updated_request_form.related_student
            department_name = user.department.name if hasattr(user, 'department') and user.department else "Phòng ban"
            title = f"Phản hồi về đơn '{updated_request_form.title}'"
            content = (
                f"{department_name} xin phản hồi về đơn '{updated_request_form.title}' của phụ huynh "
                f"{parent_user.get_full_name() or parent_user.username} - học sinh {student.user.get_full_name() if student else ''} "
                f"lớp {student.current_class.name if student and student.current_class else ''}.\n\n"
                f"Nội dung phản hồi: {updated_request_form.response_content}\n"
                f"Chi tiết xem tại mục Quản lý đơn từ."
            )
            notification = Notification.objects.create(
                title=title,
                content=content,
                sent_by=user,
                status='SENT',
                is_published=True,
                publish_time=timezone.now()
            )
            notification.target_users.add(parent_user)

            messages.success(request, f"Đã cập nhật và phản hồi cho đơn '{request_form_instance.title}'.")
            return redirect('communications:department_request_list')
    else:
        response_form = RequestFormResponseForm(instance=request_form_instance)

    context = {
        'request_form_instance': request_form_instance,
        'response_form': response_form,
        'page_title': f'Chi tiết và Phản hồi Đơn: {request_form_instance.title}'
    }
    return render(request, 'communications/department_request_detail_respond.html', context)

@login_required
def teacher_request_list(request):
    user = request.user
    # Kiểm tra xem user có phải là giáo viên không (không phân biệt hoa thường)
    if not (hasattr(user, 'role') and user.role and user.role.name and user.role.name.strip().upper() == 'TEACHER'):
        messages.error(request, "Tài khoản của bạn không phải là giáo viên hoặc chưa được gán đúng vai trò. Vui lòng liên hệ quản trị viên.")
        return redirect('homepage')

    teacher_requests = RequestForm.objects.filter(
        assigned_teachers=user
    ).order_by('submission_date')

    context = {
        'teacher_requests': teacher_requests,
        'page_title': 'Đơn từ/Kiến nghị được gán cho bạn',
    }
    return render(request, 'communications/teacher_request_list.html', context)

@login_required
def teacher_request_detail_respond(request, pk):
    user = request.user
    if not (hasattr(user, 'role') and user.role and user.role.name and user.role.name.strip().upper() == 'TEACHER'):
        raise PermissionDenied("Bạn không có quyền truy cập hoặc xử lý đơn này.")

    request_form_instance = get_object_or_404(
        RequestForm,
        pk=pk,
        assigned_teachers=user
    )

    view_only = request.GET.get('view_only') == '1'

    if view_only:
        context = {
            'request_form_instance': request_form_instance,
            'page_title': f'Chi tiết Đơn (Xem): {request_form_instance.title}',
            'view_only': True,
        }
        return render(request, 'communications/teacher_request_detail_respond.html', context)

    if request.method == 'POST':
        response_form = RequestFormResponseForm(request.POST, instance=request_form_instance)
        if response_form.is_valid():
            updated_request_form = response_form.save(commit=False)
            updated_request_form.responded_by = user
            updated_request_form.response_date = timezone.now()
            updated_request_form.save()
            messages.success(request, f"Đã cập nhật và phản hồi cho đơn '{request_form_instance.title}'.")
            return redirect('communications:teacher_request_list')
    else:
        response_form = RequestFormResponseForm(instance=request_form_instance)

    context = {
        'request_form_instance': request_form_instance,
        'response_form': response_form,
        'page_title': f'Chi tiết và Phản hồi Đơn (GV): {request_form_instance.title}',
        'view_only': False,
    }
    return render(request, 'communications/teacher_request_detail_respond.html', context)

@login_required
def conversation_list(request):
    user = request.user
    user_conversations = Conversation.objects.filter(participants=user).annotate(
        last_message_time=Max('messages__sent_at')
    ).order_by('-last_message_time', '-updated_at')

    context = {
        'conversations': user_conversations,
        'page_title': 'Hộp thư của bạn',
    }
    return render(request, 'communications/conversation_list.html', context)

@login_required
def conversation_detail(request, conversation_id):
    user = request.user
    # Đảm bảo người dùng là thành viên của cuộc hội thoại này
    conversation = get_object_or_404(Conversation, pk=conversation_id, participants=user)
    
    messages_in_conversation = conversation.messages.all().order_by('sent_at')

    if request.method == 'POST':
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            new_message = message_form.save(commit=False)
            new_message.conversation = conversation
            new_message.sender = user
            new_message.save()

            # Cập nhật trường updated_at của cuộc hội thoại
            conversation.updated_at = timezone.now() # Hoặc new_message.sent_at
            conversation.save(update_fields=['updated_at'])
            
            # messages.success(request, "Đã gửi tin nhắn!") # Có thể không cần thông báo flash cho mỗi tin nhắn
            return redirect('communications:conversation_detail', conversation_id=conversation.pk)

    else:
        message_form = MessageForm() # Form trống cho GET request

    context = {
        'conversation': conversation,
        'messages_in_conversation': messages_in_conversation,
        'message_form': message_form, # Truyền form vào context
        'page_title': f"{conversation.title or ', '.join([p.username for p in conversation.participants.all() if p != user])}",
    }
    return render(request, 'communications/conversation_detail.html', context)

@login_required
def start_new_conversation(request):
    if request.method == 'POST':
        form = StartConversationForm(request.POST, requesting_user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            initial_message_content = form.cleaned_data.get('initial_message')

            existing_conversation = Conversation.objects.annotate(
                num_participants=Count('participants')
            ).filter(
                conversation_type='DIRECT',
                participants=request.user
            ).filter(
                participants=recipient
            ).filter(
                num_participants=2 # Đảm bảo chỉ có đúng 2 người này
            ).first()

            if existing_conversation:
                conversation = existing_conversation
                messages.info(request, f"Bạn đã có cuộc hội thoại với {recipient.username}. Đang chuyển hướng...")
            else:
                # Tạo cuộc hội thoại mới
                conversation = Conversation.objects.create(conversation_type='DIRECT')
                conversation.participants.add(request.user, recipient)

            if initial_message_content:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_message_content
                )
                # Cập nhật updated_at cho conversation
                conversation.updated_at = timezone.now()
                conversation.save(update_fields=['updated_at'])
            
            return redirect('communications:conversation_detail', conversation_id=conversation.pk)
    else:
        form = StartConversationForm(requesting_user=request.user)

    context = {
        'form': form,
        'page_title': 'Bắt đầu Cuộc hội thoại mới',
    }
    return render(request, 'communications/start_new_conversation.html', context)

@login_required
def create_notification(request):
    user = request.user
    allowed_roles = ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN', 'DEPARTMENT']
    if not (hasattr(user, 'role') and user.role and user.role.name in allowed_roles):
        raise PermissionDenied("Bạn không có quyền tạo thông báo.")

    # Chọn form phù hợp
    if user.role.name == 'TEACHER':
        FormClass = TeacherNotificationForm
        # Lấy danh sách lớp chủ nhiệm và lớp dạy
        homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=user)
        taught_classes = SchoolClass.objects.filter(students__enrolled_subjects__in=user.teacher_profile.subjects_taught.all()).distinct()
        class_list_homeroom = list(homeroom_classes.order_by('name'))
        class_list_taught = list(taught_classes.order_by('name'))
        extra_context = {
            'class_list_homeroom': class_list_homeroom,
            'class_list_taught': class_list_taught,
        }
    else:
        FormClass = DepartmentNotificationForm
        # Lấy danh sách tất cả lớp
        all_classes = SchoolClass.objects.all().order_by('name')
        extra_context = {
            'class_list_all': list(all_classes),
        }

    if request.method == 'POST':
        form = FormClass(request.POST, user=user)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.sent_by = user
            notification.status = 'SENT'
            notification.is_published = True
            notification.publish_time = timezone.now()
            notification.save()
            form.save_m2m()
            messages.success(request, "Thông báo đã được tạo thành công.")
            return redirect('communications:notification_list')
    else:
        form = FormClass(user=user)

    context = {
        'form': form,
        'page_title': 'Tạo thông báo mới',
    }
    context.update(extra_context)
    return render(request, 'communications/create_notification.html', context)

@login_required
def request_detail(request, pk):
    request_form = get_object_or_404(RequestForm, pk=pk)
    
    # Kiểm tra quyền xem đơn
    if request.user != request_form.submitted_by:
        raise PermissionDenied("Bạn không có quyền xem đơn này.")
    
    context = {
        'request_form': request_form,
        'page_title': f'Chi tiết đơn: {request_form.title}',
        'show_content_only': True  # Thêm flag để template biết chỉ hiển thị nội dung
    }
    return render(request, 'communications/my_submitted_requests.html', context)

def homepage(request):
    notifications = None
    if request.user.is_authenticated:
        user = request.user
        direct_q = Q(target_users=user)
        role_q = Q()
        if hasattr(user, 'role') and user.role:
            role_q = Q(target_roles=user.role)
        class_q = Q()
        if hasattr(user, 'student_profile') and user.student_profile and hasattr(user.student_profile, 'current_class') and user.student_profile.current_class:
            class_q = Q(target_classes=user.student_profile.current_class)
        final_q = direct_q | role_q | class_q
        notifications = Notification.objects.filter(final_q, is_published=True, status='SENT').distinct().order_by('-publish_time', '-created_time')[:3]
    context = {
        'notifications': notifications,
    }
    return render(request, 'communications/home.html', context)