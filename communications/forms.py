from django import forms
from .models import RequestForm, Message, Conversation # Thêm Conversation
from accounts.models import StudentProfile, User # StudentProfile, User từ accounts.models
from school_data.models import Department # Department từ school_data.models
from django.core.exceptions import PermissionDenied
from django.db import models

class RequestFormSubmissionForm(forms.ModelForm):
    related_student = forms.ModelChoiceField(
        queryset=StudentProfile.objects.none(),
        required=True,
        label="Chọn học sinh liên quan (con của bạn)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RequestForm
        fields = ['form_type', 'title', 'content', 'related_student']
        widgets = {
            'form_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tiêu đề đơn...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nhập nội dung chi tiết...'}),
        }
        labels = {
            'form_type': 'Loại đơn/kiến nghị',
            'title': 'Tiêu đề',
            'content': 'Nội dung chi tiết',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Kiểm tra xem người dùng có phải là phụ huynh không
        if not (self.user and hasattr(self.user, 'role') and self.user.role and self.user.role.name == 'PARENT'):
            raise PermissionDenied("Chỉ phụ huynh mới được phép gửi đơn.")
        
        # Nếu là phụ huynh, hiển thị danh sách con
        if hasattr(self.user, 'parent_profile') and self.user.parent_profile:
            self.fields['related_student'].queryset = self.user.parent_profile.children.select_related('user').order_by('user__first_name', 'user__last_name')
        else:
            self.fields['related_student'].queryset = StudentProfile.objects.none()
            self.fields['related_student'].widget.attrs['disabled'] = True
            self.fields['related_student'].help_text = "Bạn cần cập nhật hồ sơ phụ huynh để chọn học sinh."

    def clean(self):
        cleaned_data = super().clean()
        form_type = cleaned_data.get('form_type')
        related_student = cleaned_data.get('related_student')

        if not related_student:
            raise forms.ValidationError(
                "Bạn phải chọn học sinh liên quan.",
                code='no_student'
            )

        # Luôn gửi cho giáo viên chủ nhiệm
        if related_student.current_class and related_student.current_class.homeroom_teacher:
            cleaned_data['assigned_teachers'] = [related_student.current_class.homeroom_teacher]
        else:
            raise forms.ValidationError(
                "Không tìm thấy giáo viên chủ nhiệm của học sinh. Vui lòng liên hệ quản trị viên.",
                code='no_homeroom_teacher'
            )

        # Tự động gán phòng ban dựa vào loại đơn
        try:
            if form_type in ['LEAVE_APPLICATION', 'GRADE_APPEAL']:
                # Đơn xin nghỉ học và đơn phúc khảo điểm -> Phòng Giáo vụ (ID: 1)
                cleaned_data['assigned_department'] = Department.objects.get(id=1)
            else:
                # Các đơn khác -> Phòng Hành chính (ID: 3)
                cleaned_data['assigned_department'] = Department.objects.get(id=3)
        except Department.DoesNotExist:
            raise forms.ValidationError(
                "Không tìm thấy phòng ban tương ứng. Vui lòng liên hệ quản trị viên.",
                code='no_department'
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.submitter = self.user
        instance.related_student = self.cleaned_data['related_student']
        
        if commit:
            instance.save()
            # Lưu các trường many-to-many
            if 'assigned_teachers' in self.cleaned_data:
                instance.assigned_teachers.set(self.cleaned_data['assigned_teachers'])
            if 'assigned_department' in self.cleaned_data:
                instance.assigned_department = self.cleaned_data['assigned_department']
                instance.save()
        
        return instance


# --- ĐẢM BẢO LỚP NÀY ĐÃ CÓ TRONG FILE communications/forms.py ---
class RequestFormResponseForm(forms.ModelForm):
    class Meta:
        model = RequestForm
        fields = ['status', 'response_content']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'response_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nhập nội dung phản hồi...'}),
        }
        labels = {
            'status': 'Cập nhật Trạng thái Đơn',
            'response_content': 'Nội dung Phản hồi',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_statuses = [
            ('PROCESSING', 'Đang xử lý'),
            ('RESOLVED', 'Đã giải quyết'),
            ('REJECTED', 'Đã từ chối'),
            ('CLOSED', 'Đã đóng'),
        ]
        self.fields['status'].choices = [choice for choice in allowed_statuses if choice[0] in dict(RequestForm.STATUS_CHOICES).keys()]
        if self.instance and self.instance.pk and self.instance.status == 'SUBMITTED':
             self.fields['status'].initial = 'PROCESSING'
# --- KẾT THÚC ĐỊNH NGHĨA RequestFormResponseForm ---

from django import forms
from .models import RequestForm, Message # Thêm Message vào import
from accounts.models import StudentProfile, User 
from school_data.models import Department

class RequestFormSubmissionForm(forms.ModelForm):
    # ... (code của RequestFormSubmissionForm đã có) ...
    related_student_for_parent = forms.ModelChoiceField(
        queryset=StudentProfile.objects.none(), 
        required=False,
        label="Học sinh liên quan (nếu bạn là Phụ huynh)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False, 
        label="Gửi đến Phòng Ban",
        empty_label="--- Chọn Phòng Ban (Tùy chọn) ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role__name='TEACHER', is_active=True).select_related('role').order_by('last_name', 'first_name'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        required=False,
        label="Hoặc/Và Gửi đến Giáo viên (chọn một hoặc nhiều)",
        help_text="Bạn có thể chọn gửi đơn này cho Phòng Ban và/hoặc một hoặc nhiều Giáo viên."
    )
    class Meta:
        model = RequestForm
        fields = ['form_type', 'title', 'content', 'related_student_for_parent', 'assigned_department', 'assigned_teachers']
        widgets = {
            'form_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tiêu đề đơn...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nhập nội dung chi tiết...'}),
        }
        labels = {
            'form_type': 'Loại đơn/kiến nghị',
            'title': 'Tiêu đề',
            'content': 'Nội dung chi tiết',
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'role') and user.role and user.role.name == 'PARENT':
            if hasattr(user, 'parent_profile') and user.parent_profile:
                self.fields['related_student_for_parent'].queryset = user.parent_profile.children.select_related('user').order_by('user__first_name', 'user__last_name')
                self.fields['related_student_for_parent'].label = "Chọn học sinh liên quan (con của bạn)"
            else:
                self.fields['related_student_for_parent'].queryset = StudentProfile.objects.none()
                self.fields['related_student_for_parent'].widget.attrs['disabled'] = True
                self.fields['related_student_for_parent'].help_text = "Bạn cần cập nhật hồ sơ phụ huynh để chọn học sinh."
        else:
            if 'related_student_for_parent' in self.fields:
                 del self.fields['related_student_for_parent']
    def clean(self):
        cleaned_data = super().clean()
        form_type = cleaned_data.get('form_type')
        related_student = cleaned_data.get('related_student_for_parent')

        if not related_student:
            raise forms.ValidationError(
                "Bạn phải chọn học sinh liên quan.",
                code='no_student'
            )

        # Luôn gửi cho giáo viên chủ nhiệm
        if related_student.current_class and related_student.current_class.homeroom_teacher:
            cleaned_data['assigned_teachers'] = [related_student.current_class.homeroom_teacher]
        else:
            raise forms.ValidationError(
                "Không tìm thấy giáo viên chủ nhiệm của học sinh. Vui lòng liên hệ quản trị viên.",
                code='no_homeroom_teacher'
            )

        # Tự động gán phòng ban dựa vào loại đơn
        try:
            if form_type in ['LEAVE_APPLICATION', 'GRADE_APPEAL']:
                # Đơn xin nghỉ học và đơn phúc khảo điểm -> Phòng Giáo vụ (ID: 1)
                cleaned_data['assigned_department'] = Department.objects.get(id=1)
            else:
                # Các đơn khác -> Phòng Hành chính (ID: 3)
                cleaned_data['assigned_department'] = Department.objects.get(id=3)
        except Department.DoesNotExist:
            raise forms.ValidationError(
                "Không tìm thấy phòng ban tương ứng. Vui lòng liên hệ quản trị viên.",
                code='no_department'
            )

        return cleaned_data

class RequestFormResponseForm(forms.ModelForm):
    # ... (code của RequestFormResponseForm đã có) ...
    class Meta:
        model = RequestForm
        fields = ['status', 'response_content']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'response_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nhập nội dung phản hồi...'}),
        }
        labels = {
            'status': 'Cập nhật Trạng thái Đơn',
            'response_content': 'Nội dung Phản hồi',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_statuses = [
            ('PROCESSING', 'Đang xử lý'),
            ('RESOLVED', 'Đã giải quyết'),
            ('REJECTED', 'Đã từ chối'),
            ('CLOSED', 'Đã đóng'),
        ]
        # Đảm bảo rằng các choices này thực sự tồn tại trong RequestForm.STATUS_CHOICES
        valid_choices = [choice for choice in allowed_statuses if choice[0] in dict(RequestForm.STATUS_CHOICES).keys()]
        self.fields['status'].choices = valid_choices
        
        if self.instance and self.instance.pk and self.instance.status == 'SUBMITTED':
             self.fields['status'].initial = 'PROCESSING'


# --- FORM MỚI CHO TIN NHẮN ---
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content'] # Chỉ cần trường nội dung từ người dùng
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Nhập tin nhắn của bạn...'
            })
        }
        labels = {
            'content': '' # Không cần label nếu placeholder đã rõ ràng
        }
# --- KẾT THÚC FORM MỚI ---
from django import forms
from .models import RequestForm, Message, Conversation # Thêm Conversation
from accounts.models import StudentProfile, User 
from school_data.models import Department

# ... (RequestFormSubmissionForm, RequestFormResponseForm, MessageForm đã có ở trên) ...

class StartConversationForm(forms.Form):
    # Trường để chọn người dùng muốn chat cùng
    # Chúng ta sẽ loại trừ chính người dùng hiện tại khỏi danh sách lựa chọn
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(), # Sẽ được cập nhật trong __init__
        label="Trò chuyện với",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- Chọn người dùng ---"
    )
    # Trường tùy chọn cho tin nhắn đầu tiên
    initial_message = forms.CharField(
        label="Tin nhắn đầu tiên (tùy chọn)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nhập tin nhắn đầu tiên của bạn...'}),
    )

    def __init__(self, *args, **kwargs):
        requesting_user = kwargs.pop('requesting_user', None) # Lấy user hiện tại từ view
        super().__init__(*args, **kwargs)
        from accounts.models import Role, StudentProfile, ParentProfile, User
        from school_data.models import Class as SchoolClass, Subject as SchoolSubject
        if requesting_user:
            base_qs = User.objects.filter(is_active=True).exclude(pk=requesting_user.pk)
            role_name = getattr(requesting_user.role, 'name', None) if hasattr(requesting_user, 'role') and requesting_user.role else None
            # 1. Giáo viên: gửi tới tất cả user (trừ admin)
            if role_name == 'TEACHER':
                self.fields['recipient'].queryset = base_qs.exclude(role__name='ADMIN')
            # 2. Phòng ban: gửi tới user phòng ban khác và giáo viên
            elif role_name == 'DEPARTMENT':
                my_department_id = getattr(requesting_user.department, 'id', None) if hasattr(requesting_user, 'department') and requesting_user.department else None
                self.fields['recipient'].queryset = base_qs.filter(
                    (
                        models.Q(is_staff=True, department__isnull=False) & ~models.Q(department__id=my_department_id)
                    ) | models.Q(role__name='TEACHER')
                ).exclude(role__name__in=['PARENT', 'STUDENT'])
            # 3. Phụ huynh: gửi tới giáo viên chủ nhiệm, giáo viên dạy con, phụ huynh cùng lớp
            elif role_name == 'PARENT':
                try:
                    parent_profile = ParentProfile.objects.get(user=requesting_user)
                    children = parent_profile.children.all()
                    class_ids = set()
                    teacher_ids = set()
                    parent_ids = set()
                    for child in children:
                        if child.current_class:
                            class_ids.add(child.current_class.pk)
                            # Giáo viên chủ nhiệm
                            if child.current_class.homeroom_teacher:
                                teacher_ids.add(child.current_class.homeroom_teacher.pk)
                            # Giáo viên dạy các môn
                            for subj in child.enrolled_subjects.all():
                                for t in subj.teachers.all():
                                    teacher_ids.add(t.user.pk)
                    # Phụ huynh cùng lớp
                    parent_ids = set(ParentProfile.objects.filter(children__current_class__pk__in=class_ids).exclude(user=requesting_user).values_list('user__pk', flat=True))
                    self.fields['recipient'].queryset = base_qs.filter(
                        models.Q(pk__in=teacher_ids) | models.Q(pk__in=parent_ids)
                    )
                except ParentProfile.DoesNotExist:
                    self.fields['recipient'].queryset = base_qs.none()
            # 4. Học sinh: gửi tới giáo viên chủ nhiệm, giáo viên dạy mình
            elif role_name == 'STUDENT':
                try:
                    student_profile = StudentProfile.objects.get(user=requesting_user)
                    teacher_ids = set()
                    if student_profile.current_class and student_profile.current_class.homeroom_teacher:
                        teacher_ids.add(student_profile.current_class.homeroom_teacher.pk)
                    for subj in student_profile.enrolled_subjects.all():
                        for t in subj.teachers.all():
                            teacher_ids.add(t.user.pk)
                    self.fields['recipient'].queryset = base_qs.filter(pk__in=teacher_ids)
                except StudentProfile.DoesNotExist:
                    self.fields['recipient'].queryset = base_qs.none()
            else:
                self.fields['recipient'].queryset = base_qs
        else:
            self.fields['recipient'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['recipient'].label_from_instance = lambda obj: obj.get_full_name() or obj.username


from django import forms
from .models import Notification, Message, Conversation, RequestForm # Đảm bảo Notification đã import
from accounts.models import User, Role, StudentProfile # Import Role
from school_data.models import Department, Class as SchoolClass # Import Class

# ... (các form khác đã có) ...

class NotificationForm(forms.ModelForm):
    # Trường lựa chọn nhóm đối tượng chung
    RECIPIENT_GROUP_CHOICES = [
        ('', '--- Chọn nhóm chung (tùy chọn) ---'),
        ('ALL_TEACHERS', 'Tất cả Giáo viên'),
        ('ALL_PARENTS', 'Tất cả Phụ huynh'),
        ('ALL_STUDENTS', 'Tất cả Học sinh'),
        # ('EVERYONE', 'Tất cả mọi người trong trường'), # Cân nhắc kỹ logic cho lựa chọn này
    ]
    recipient_group = forms.ChoiceField(
        choices=RECIPIENT_GROUP_CHOICES,
        required=False,
        label="Gửi đến nhóm chung",
        widget=forms.Select(attrs={'class': 'form-control mb-2'})
    )

    # Trường chọn nhiều vai trò cụ thể (ngoài các nhóm chung ở trên)
    target_roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple, # Hoặc SelectMultiple(attrs={'class': 'form-control select2-multiple', 'size':'3'})
        required=False,
        label="Hoặc/Và chọn các Vai trò cụ thể",
        help_text="Giữ Ctrl (hoặc Command trên Mac) để chọn nhiều."
    )

    # Trường chọn nhiều lớp học cụ thể
    target_classes = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple, # Hoặc SelectMultiple
        required=False,
        label="Hoặc/Và chọn các Lớp học cụ thể",
        help_text="Giữ Ctrl (hoặc Command trên Mac) để chọn nhiều."
    )
    
    # Trường chọn nhiều người dùng cụ thể
    target_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2-multiple-users', 'size':'5'}), # Cần JS cho select2
        required=False,
        label="Hoặc/Và chọn Người dùng cụ thể",
        help_text="Giữ Ctrl (hoặc Command trên Mac) để chọn nhiều. Bạn có thể tìm kiếm nếu dùng widget nâng cao."
    )

    class Meta:
        model = Notification
        fields = ['title', 'content', 'recipient_group', 'target_roles', 'target_classes', 'target_users']
        # Các trường 'sent_by', 'status', 'publish_time', 'is_published' sẽ được xử lý trong view.
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tiêu đề thông báo...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 7, 'placeholder': 'Nhập nội dung thông báo...'}),
        }
        labels = {
            'title': 'Tiêu đề Thông báo',
            'content': 'Nội dung chi tiết',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh label_from_instance cho các trường ModelMultipleChoiceField nếu cần
        self.fields['target_roles'].label_from_instance = lambda obj: obj.get_name_display()
        self.fields['target_classes'].label_from_instance = lambda obj: f"{obj.name} ({obj.academic_year or 'N/A'})"
        self.fields['target_users'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
        
        # Gợi ý: Để widget SelectMultiple cho target_users thân thiện hơn khi có nhiều user,
        # bạn có thể dùng các thư viện như django-select2 hoặc tự viết widget với tìm kiếm.
        # Hiện tại, nó sẽ là một danh sách dài.

    def clean(self):
        cleaned_data = super().clean()
        recipient_group = cleaned_data.get('recipient_group')
        target_roles = cleaned_data.get('target_roles')
        target_classes = cleaned_data.get('target_classes')
        target_users = cleaned_data.get('target_users')

        if not recipient_group and not target_roles and not target_classes and not target_users:
            raise forms.ValidationError(
                "Bạn phải chọn ít nhất một hình thức gửi đến (Nhóm chung, Vai trò, Lớp, hoặc Người dùng cụ thể).",
                code='no_recipient_selected'
            )
        return cleaned_data