from django import forms
from .models import Score # Score được định nghĩa trong academic_records.models

# Import các model từ các app khác
from accounts.models import StudentProfile, User 
from school_data.models import Class as SchoolClass, Subject as SchoolSubject # Đổi tên để tránh nhầm lẫn

class ScoreContextForm(forms.Form):
    """
    Form để Giáo viên chọn các thông tin chung (context) trước khi nhập điểm.
    """
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(), 
        label="Chọn Lớp học",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- Chọn Lớp ---"
    )
    subject = forms.ModelChoiceField(
        queryset=SchoolSubject.objects.none(), 
        label="Chọn Môn học",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- Chọn Môn ---"
    )
    exam_type = forms.ChoiceField(
        choices=Score.EXAM_TYPE_CHOICES,
        label="Loại Kỳ thi/Kiểm tra",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    exam_date = forms.DateField(
        label="Ngày thi/Kiểm tra",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Chọn ngày thi hoặc ngày kiểm tra."
    )
    # academic_period = forms.CharField(
    #     max_length=50,
    #     required=False, 
    #     label="Kỳ học/Năm học (VD: HK1 2024-2025)",
    #     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: HK1 2024-2025'}),
    #     help_text="Để trống nếu không áp dụng cho kỳ học cụ thể."
    # )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None) 
        super().__init__(*args, **kwargs)
        
        self.fields['school_class'].queryset = SchoolClass.objects.all().order_by('name')
        self.fields['subject'].queryset = SchoolSubject.objects.all().order_by('name')

        if teacher:
            if hasattr(teacher, 'teacher_profile') and teacher.teacher_profile:
                self.fields['subject'].queryset = teacher.teacher_profile.subjects_taught.all().order_by('name')
                if not self.fields['subject'].queryset.exists():
                     self.fields['subject'].help_text = "Bạn chưa được phân công giảng dạy môn nào."
            else: 
                self.fields['subject'].queryset = SchoolSubject.objects.none()
                self.fields['subject'].help_text = "Không tìm thấy hồ sơ giáo viên hoặc bạn chưa được phân công môn dạy."
        
        if self.data.get('school_class'):
            try:
                selected_class_pk = int(self.data.get('school_class'))
                self.fields['school_class'].initial = selected_class_pk
            except (ValueError, TypeError):
                pass 
        
        if self.data.get('subject'):
            try:
                self.fields['subject'].initial = int(self.data.get('subject'))
            except (ValueError, TypeError):
                pass


class ScoreEntryForm(forms.ModelForm):
    """
    Form cho một mục điểm của một học sinh.
    Sẽ được sử dụng trong modelformset_factory.
    """
    # Fields không phải là một phần của Score model, nhưng cần cho hiển thị/logic
    student_name = forms.CharField(
        label="Học sinh", 
        required=False, 
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext bg-light p-1 border rounded'})
    )
    student_id = forms.IntegerField(widget=forms.HiddenInput(), required=True) # Bắt buộc để biết điểm này của ai

    class Meta:
        model = Score
        fields = ['score_value', 'notes'] # Chỉ các trường của model Score mà người dùng sẽ nhập
        widgets = {
            'score_value': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0', 'max': '10'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 1, 'placeholder': 'Ghi chú (nếu có)'}),
        }
        labels = {
            'score_value': 'Điểm',
            'notes': 'Ghi chú',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nếu form được khởi tạo với một instance Score đã có (khi load điểm cũ để sửa)
        if self.instance and self.instance.pk and self.instance.student:
            self.fields['student_name'].initial = self.instance.student.user.get_full_name() or self.instance.student.user.username
            self.fields['student_id'].initial = self.instance.student.pk
        # Nếu form được khởi tạo với initial data (khi tạo formset cho danh sách học sinh mới)
        # modelformset_factory sẽ truyền initial data vào từng form instance.
        # Các trường của form sẽ tự động lấy giá trị từ self.initial nếu key khớp.
        # Ví dụ, nếu self.initial = {'student_id': X, 'student_name': 'Y'},
        # thì self.fields['student_id'].initial và self.fields['student_name'].initial sẽ được tự động gán.
        # Chúng ta không cần gán lại một cách tường minh ở đây nếu initial data được cung cấp đúng cho formset.
from django import forms
from .models import Score, RewardAndDiscipline, Evaluation # Thêm RewardAndDiscipline
from accounts.models import StudentProfile, User 
from school_data.models import Class as SchoolClass, Subject as SchoolSubject

# ... (ScoreContextForm, ScoreEntryForm đã có) ...

class RewardAndDisciplineForm(forms.ModelForm):
    class Meta:
        model = RewardAndDiscipline
        fields = ['student', 'record_type', 'date_issued', 'reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}), # Sẽ tốt hơn nếu dùng autocomplete hoặc raw_id
            'record_type': forms.Select(attrs={'class': 'form-control'}),
            'date_issued': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'student': 'Chọn Học sinh',
            'record_type': 'Loại (Khen thưởng/Kỷ luật)',
            'date_issued': 'Ngày Quyết định',
            'reason': 'Nội dung/Lý do chi tiết',
        }

    def __init__(self, *args, **kwargs):
        requesting_user = kwargs.pop('requesting_user', None) # Lấy user từ view
        super().__init__(*args, **kwargs)
        
        # Giới hạn danh sách học sinh nếu người dùng là giáo viên chủ nhiệm
        # hoặc cho phép chọn từ tất cả nếu là phòng ban/admin
        if requesting_user and hasattr(requesting_user, 'role') and requesting_user.role:
            if requesting_user.role.name == 'TEACHER':
                # Lấy các lớp mà giáo viên này chủ nhiệm
                homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=requesting_user)
                if homeroom_classes.exists():
                    # Chỉ cho phép chọn học sinh từ các lớp chủ nhiệm
                    self.fields['student'].queryset = StudentProfile.objects.filter(
                        current_class__in=homeroom_classes
                    ).select_related('user').order_by('user__last_name', 'user__first_name')
                else:
                    # Nếu không chủ nhiệm lớp nào, không cho chọn học sinh
                    self.fields['student'].queryset = StudentProfile.objects.none()
                    self.fields['student'].help_text = "Bạn không chủ nhiệm lớp nào để tạo khen thưởng/kỷ luật."
            elif requesting_user.role.name in ['SCHOOL_ADMIN', 'ADMIN']:
                # Cho phép chọn từ tất cả học sinh
                self.fields['student'].queryset = StudentProfile.objects.select_related('user').order_by('user__last_name', 'user__first_name')
            else: # Các vai trò khác không được chọn
                self.fields['student'].queryset = StudentProfile.objects.none()
        else: # Mặc định nếu không có user hoặc role
            self.fields['student'].queryset = StudentProfile.objects.all().select_related('user').order_by('user__last_name', 'user__first_name')

        self.fields['student'].label_from_instance = lambda obj: obj.user.get_full_name() or obj.user.username


from django import forms
from .models import Score, RewardAndDiscipline, Evaluation # Đảm bảo Evaluation đã được import
from accounts.models import StudentProfile, User 
from school_data.models import Class as SchoolClass, Subject as SchoolSubject # Đổi tên để tránh nhầm lẫn

# ... (ScoreContextForm, ScoreEntryForm, RewardAndDisciplineForm đã có) ...

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        # Các trường 'evaluator' (người đánh giá) và 'evaluation_date' (ngày đánh giá)
        # sẽ được tự động gán trong view khi lưu.
        fields = ['student', 'subject', 'evaluation_type', 'content']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}), # Cân nhắc dùng autocomplete/raw_id nếu danh sách HS dài
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'evaluation_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Nhập nội dung đánh giá/nhận xét chi tiết...'}),
        }
        labels = {
            'student': 'Chọn Học sinh để Đánh giá',
            'subject': 'Môn học (nếu là nhận xét cho môn học cụ thể)',
            'evaluation_type': 'Loại Đánh giá/Nhận xét',
            'content': 'Nội dung chi tiết',
        }
        help_texts = {
            'subject': 'Để trống nếu đây là đánh giá chung (ví dụ: hạnh kiểm, nhận xét tổng kết cuối kỳ).',
        }

    def __init__(self, *args, **kwargs):
        requesting_user = kwargs.pop('requesting_user', None) # Lấy user giáo viên từ view
        super().__init__(*args, **kwargs)

        # Giới hạn danh sách học sinh mà giáo viên này có thể đánh giá
        # Logic này cần được tùy chỉnh dựa trên cách bạn phân công giảng dạy/chủ nhiệm
        if requesting_user and hasattr(requesting_user, 'role') and requesting_user.role:
            if requesting_user.role.name == 'TEACHER':
                # Ví dụ: Lấy học sinh từ các lớp giáo viên này chủ nhiệm
                homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=requesting_user)
                
                # (Nâng cao) Lấy học sinh từ các lớp giáo viên này giảng dạy các môn họ phụ trách
                # student_pks_from_taught_subjects = set()
                # if hasattr(requesting_user, 'teacher_profile'):
                #     for subject_taught in requesting_user.teacher_profile.subjects_taught.all():
                #         # Giả sử có một model liên kết Subject với Class (ví dụ: ClassSubjectAssignment)
                #         # Hoặc StudentProfile có ManyToManyField 'enrolled_subjects'
                #         students_learning_subject = StudentProfile.objects.filter(enrolled_subjects=subject_taught)
                #         student_pks_from_taught_subjects.update(students_learning_subject.values_list('pk', flat=True))
                
                # Kết hợp học sinh từ lớp chủ nhiệm và lớp giảng dạy (nếu có logic đó)
                # student_queryset = StudentProfile.objects.filter(
                # Q(current_class__in=homeroom_classes) | Q(pk__in=list(student_pks_from_taught_subjects))
                # ).distinct().select_related('user').order_by('current_class__name', 'user__last_name', 'user__first_name')

                if homeroom_classes.exists():
                    self.fields['student'].queryset = StudentProfile.objects.filter(
                        current_class__in=homeroom_classes
                    ).select_related('user').order_by('current_class__name', 'user__last_name', 'user__first_name')
                    self.fields['student'].help_text = "Hiển thị học sinh từ các lớp bạn chủ nhiệm."
                else:
                    # Nếu không chủ nhiệm, có thể cho phép chọn từ tất cả (nếu có quyền khác) hoặc không cho chọn
                    # Tạm thời để trống nếu không chủ nhiệm lớp nào
                    self.fields['student'].queryset = StudentProfile.objects.none() # Hoặc tất cả nếu có quyền
                    self.fields['student'].help_text = "Bạn hiện không chủ nhiệm lớp nào để chọn học sinh."


                # Lọc danh sách môn học (có thể là các môn giáo viên này dạy)
                if hasattr(requesting_user, 'teacher_profile'):
                    self.fields['subject'].queryset = requesting_user.teacher_profile.subjects_taught.all().order_by('name')
                else: # Nếu không có teacher_profile, có thể lấy tất cả môn học
                    self.fields['subject'].queryset = SchoolSubject.objects.all().order_by('name')
                self.fields['subject'].empty_label = "--- Chọn môn học (nếu có) ---"

            elif requesting_user.role.name in ['SCHOOL_ADMIN', 'ADMIN']: # Các vai trò quản lý có thể chọn bất kỳ HS nào
                 self.fields['student'].queryset = StudentProfile.objects.select_related('user').order_by('current_class__name', 'user__last_name', 'user__first_name')
                 self.fields['subject'].queryset = SchoolSubject.objects.all().order_by('name')
                 self.fields['subject'].empty_label = "--- Chọn môn học (nếu có) ---"
            else: # Các vai trò khác không được chọn
                self.fields['student'].queryset = StudentProfile.objects.none()
                self.fields['subject'].queryset = SchoolSubject.objects.none()
        else: # Mặc định nếu không có user hoặc role
            self.fields['student'].queryset = StudentProfile.objects.all().select_related('user').order_by('current_class__name', 'user__last_name', 'user__first_name')
            self.fields['subject'].queryset = SchoolSubject.objects.all().order_by('name')

        self.fields['student'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username} (Lớp: {obj.current_class.name if obj.current_class else 'N/A'})"
        self.fields['subject'].required = False # Môn học không bắt buộc cho tất cả các loại đánh giá
