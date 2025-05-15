from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Max, Case, When, Value, IntegerField
from django.forms import modelformset_factory 
from django.urls import reverse
from collections import defaultdict
import json 

from .models import Score, RewardAndDiscipline, Evaluation # Đảm bảo Evaluation được import
from accounts.models import StudentProfile, ParentProfile, User, Role
from school_data.models import Class as SchoolClass, Subject as SchoolSubject, Department
from .forms import ScoreContextForm, ScoreEntryForm, RewardAndDisciplineForm, EvaluationForm # Đảm bảo EvaluationForm được import
from communications.models import Notification

def convert_defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        return {k: convert_defaultdict_to_dict(v) for k, v in d.items()}
    return d

@login_required
def view_scores(request):
    user = request.user
    context = {
        'page_title': 'Bảng điểm của bạn',
        'scores_by_student_subject': {},
        'is_parent': False,
        'students_to_view': [],
        'error_message': None
    }
    user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') else None
    
    if user_role_name == 'STUDENT':
        try:
            student_profile = user.student_profile
            context['students_to_view'] = [student_profile]
            context['page_title'] = f'Bảng điểm của {student_profile.user.get_full_name() or student_profile.user.username}'
        except StudentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ học sinh của bạn."
    elif user_role_name == 'PARENT':
        context['is_parent'] = True
        try:
            parent_profile = ParentProfile.objects.get(user=user)
            children_profiles_qs = parent_profile.children.all().select_related('user')
            if not children_profiles_qs.exists():
                context['error_message'] = "Bạn chưa có thông tin học sinh nào được liên kết."
            else:
                context['students_to_view'] = list(children_profiles_qs)
                context['page_title'] = 'Bảng điểm của các con'
        except ParentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ phụ huynh của bạn."
        except Exception:
            context['error_message'] = "Đã có lỗi xảy ra khi truy xuất thông tin phụ huynh."
    else:
        context['error_message'] = "Chức năng này chỉ dành cho Học sinh và Phụ huynh."

    scores_data_restructured = defaultdict(lambda: defaultdict(lambda: {'subject_name': '', 'teacher_names': '', 'scores': []}))

    if context['students_to_view']:
        student_profile_pks = [sp.pk for sp in context['students_to_view']]
        scores_qs = Score.objects.filter(student_id__in=student_profile_pks)\
            .select_related('subject', 'student__user')\
            .prefetch_related('subject__teachers__user')\
            .order_by('student__user__username', 'subject__name', 'exam_date', 'exam_type')

        for score_item in scores_qs:
            student_display_name = score_item.student.user.get_full_name() or score_item.student.user.username
            subject_obj = score_item.subject
            subject_pk = subject_obj.pk

            if not scores_data_restructured[student_display_name][subject_pk]['subject_name']:
                scores_data_restructured[student_display_name][subject_pk]['subject_name'] = subject_obj.name
                
                teacher_names_list = []
                for teacher_profile in subject_obj.teachers.all():
                    teacher_user = teacher_profile.user
                    teacher_name = teacher_user.get_full_name() or teacher_user.username
                    teacher_names_list.append(teacher_name)
                scores_data_restructured[student_display_name][subject_pk]['teacher_names'] = ", ".join(sorted(list(set(teacher_names_list)))) or "N/A"

            scores_data_restructured[student_display_name][subject_pk]['scores'].append(score_item)
            
    final_scores_data = {}
    for student_name, subject_map in scores_data_restructured.items():
        final_scores_data[student_name] = {}
        for subject_pk, data in subject_map.items():
            final_scores_data[student_name][subject_pk] = {
                'subject_name': data['subject_name'],
                'teacher_names': data['teacher_names'],
                'scores': data['scores']
            }
    context['scores_by_student_subject'] = final_scores_data
    return render(request, 'academic_records/view_scores.html', context)

@login_required
def enter_scores(request):
    # ... (code enter_scores không thay đổi so với phiên bản hoạt động gần nhất) ...
    teacher = request.user
    if not (hasattr(teacher, 'role') and teacher.role and teacher.role.name == 'TEACHER'):
        raise PermissionDenied("Chức năng này chỉ dành cho Giáo Viên.")

    score_context_form = ScoreContextForm(request.GET or None, teacher=teacher)
    ScoreFormSet_default = modelformset_factory(Score, form=ScoreEntryForm, extra=0)
    score_formset = ScoreFormSet_default(queryset=Score.objects.none()) 
    
    students_for_scoring = []
    selected_class_id = request.GET.get('school_class')
    selected_subject_id = request.GET.get('subject')
    selected_exam_type = request.GET.get('exam_type')
    selected_exam_date = request.GET.get('exam_date')

    if request.method == 'POST':
        post_selected_class_id = request.POST.get('selected_class_id_hidden')
        post_selected_subject_id = request.POST.get('selected_subject_id_hidden')
        post_selected_exam_type = request.POST.get('selected_exam_type_hidden')
        post_selected_exam_date = request.POST.get('selected_exam_date_hidden')

        score_context_form = ScoreContextForm(initial={
            'school_class': post_selected_class_id, 'subject': post_selected_subject_id,
            'exam_type': post_selected_exam_type, 'exam_date': post_selected_exam_date,
        }, teacher=teacher)

        if post_selected_class_id:
            target_class = get_object_or_404(SchoolClass, pk=post_selected_class_id)
            students_for_scoring = StudentProfile.objects.filter(current_class=target_class).select_related('user').order_by('user__last_name', 'user__first_name')
        
        num_forms_for_post = len(students_for_scoring) if students_for_scoring else 0
        ScoreFormSet_post = modelformset_factory(Score, form=ScoreEntryForm, extra=num_forms_for_post, can_delete=False)
        score_formset = ScoreFormSet_post(request.POST, queryset=Score.objects.none())

        if score_formset.is_valid():
            saved_count = 0
            updated_count = 0
            subject_instance = get_object_or_404(SchoolSubject, pk=post_selected_subject_id)

            for form_in_formset in score_formset:
                if form_in_formset.has_changed() and form_in_formset.cleaned_data.get('score_value') is not None:
                    student_id = form_in_formset.cleaned_data.get('student_id')
                    score_value = form_in_formset.cleaned_data.get('score_value')
                    notes = form_in_formset.cleaned_data.get('notes', '')

                    if student_id:
                        student_profile = get_object_or_404(StudentProfile, pk=student_id)
                        score_entry, created = Score.objects.update_or_create(
                            student=student_profile, subject=subject_instance,
                            exam_type=post_selected_exam_type, exam_date=post_selected_exam_date,
                            defaults={'score_value': score_value, 'notes': notes}
                        )
                        if created: saved_count += 1
                        else: updated_count += 1
            
            if saved_count > 0 or updated_count > 0:
                messages.success(request, f"Đã lưu {saved_count} điểm mới và cập nhật {updated_count} điểm thành công!")
            else:
                messages.info(request, "Không có thay đổi nào được thực hiện hoặc không có điểm nào được nhập.")
            
            redirect_url_params = (f"?school_class={post_selected_class_id}&subject={post_selected_subject_id}"
                                   f"&exam_type={post_selected_exam_type}&exam_date={post_selected_exam_date}")
            return redirect(reverse('academic_records:enter_scores') + redirect_url_params)
        else:
            messages.error(request, "Vui lòng kiểm tra lại các lỗi trong bảng điểm.")

    elif score_context_form.is_valid() and selected_class_id and selected_subject_id and selected_exam_type and selected_exam_date:
        target_class = get_object_or_404(SchoolClass, pk=selected_class_id)
        target_subject = get_object_or_404(SchoolSubject, pk=selected_subject_id)
        
        students_for_scoring = StudentProfile.objects.filter(current_class=target_class).select_related('user').order_by('user__last_name', 'user__first_name')

        initial_data_for_formset = []
        if students_for_scoring.exists():
            for student_profile in students_for_scoring:
                existing_score = Score.objects.filter(
                    student=student_profile, subject=target_subject,
                    exam_type=selected_exam_type, exam_date=selected_exam_date,
                ).first()
                initial_data_for_formset.append({
                    'student_id': student_profile.pk,
                    'student_name': student_profile.user.get_full_name() or student_profile.user.username,
                    'score_value': existing_score.score_value if existing_score else None,
                    'notes': existing_score.notes if existing_score else '',
                })
            
            num_forms_to_create = len(initial_data_for_formset)
            ScoreFormSet_get = modelformset_factory(Score, form=ScoreEntryForm, extra=num_forms_to_create, can_delete=False)
            score_formset = ScoreFormSet_get(queryset=Score.objects.none(), initial=initial_data_for_formset)
        
    context = {
        'score_context_form': score_context_form,
        'score_formset': score_formset,
        'students_for_scoring': students_for_scoring,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id,
        'selected_exam_type': selected_exam_type,
        'selected_exam_date': selected_exam_date,
        'page_title': 'Nhập Điểm cho Học sinh'
    }
    return render(request, 'academic_records/enter_scores.html', context)

@login_required
def teacher_view_class_scores(request):
    # ... (code teacher_view_class_scores không thay đổi) ...
    teacher = request.user
    if not (hasattr(teacher, 'role') and teacher.role and teacher.role.name == 'TEACHER'):
        raise PermissionDenied("Chức năng này chỉ dành cho Giáo viên.")

    homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=teacher)
    
    selected_class_pk_from_get = request.GET.get('class_to_view')
    active_class = None
    
    if selected_class_pk_from_get:
        active_class = get_object_or_404(SchoolClass, pk=selected_class_pk_from_get, homeroom_teacher=teacher)
    elif homeroom_classes.exists():
        active_class = homeroom_classes.first()

    students_in_class = []
    scores_data_defaultdict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    if active_class:
        students_in_class = StudentProfile.objects.filter(current_class=active_class).select_related('user').order_by('user__last_name', 'user__first_name')
        if students_in_class.exists():
            student_pks = [sp.pk for sp in students_in_class]
            scores_qs = Score.objects.filter(student_id__in=student_pks).select_related('subject', 'student__user').order_by('student__user__last_name', 'student__user__first_name', 'academic_period', 'subject__name', 'exam_date')
            
            for score_item in scores_qs:
                student_display_name = score_item.student.user.get_full_name() or score_item.student.user.username
                period = score_item.academic_period or "Chưa xác định kỳ học"
                subject_name = score_item.subject.name
                scores_data_defaultdict[student_display_name][period][subject_name].append(score_item)
    else:
        if homeroom_classes.exists():
             messages.info(request, "Vui lòng chọn một lớp chủ nhiệm để xem điểm.")
        else:
            messages.info(request, "Bạn hiện không chủ nhiệm lớp nào để xem điểm.")

    context = {
        'page_title': f'Bảng điểm Lớp {active_class.name}' if active_class else 'Xem Điểm Lớp Chủ Nhiệm',
        'active_class': active_class,
        'homeroom_classes': homeroom_classes,
        'scores_by_student_period_subject': convert_defaultdict_to_dict(scores_data_defaultdict),
        'students_in_class': students_in_class 
    }
    return render(request, 'academic_records/teacher_view_class_scores.html', context)

@login_required
def view_reward_discipline(request):
    # ... (code view_reward_discipline không thay đổi) ...
    user = request.user
    context = {
        'page_title': 'Khen thưởng và Kỷ luật',
        'records_by_student': defaultdict(list), 
        'is_parent': False,
        'students_to_view': [], 
        'error_message': None
    }

    user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') else None
    
    if user_role_name == 'STUDENT':
        try:
            student_profile = user.student_profile
            context['students_to_view'] = [student_profile]
            context['page_title'] = f'Khen thưởng/Kỷ luật của {student_profile.user.get_full_name() or student_profile.user.username}'
        except StudentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ học sinh của bạn."
    elif user_role_name == 'PARENT':
        context['is_parent'] = True
        try:
            parent_profile = ParentProfile.objects.get(user=user)
            children_profiles_qs = parent_profile.children.all().select_related('user')
            if not children_profiles_qs.exists():
                context['error_message'] = "Bạn chưa có thông tin học sinh nào được liên kết."
            else:
                context['students_to_view'] = list(children_profiles_qs)
                context['page_title'] = 'Khen thưởng/Kỷ luật của các con'
        except ParentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ phụ huynh của bạn."
    else:
        context['error_message'] = "Chức năng này chỉ dành cho Học sinh và Phụ huynh."

    if context['students_to_view']:
        student_pks = [sp.pk for sp in context['students_to_view']]
        records_qs = RewardAndDiscipline.objects.filter(
            student_id__in=student_pks
        ).select_related('student__user', 'issued_by').order_by('student__user__username', '-date_issued')
        
        for record in records_qs:
            student_display_name = record.student.user.get_full_name() or record.student.user.username
            context['records_by_student'][student_display_name].append(record)
    context['records_by_student'] = dict(context['records_by_student'])
    return render(request, 'academic_records/view_reward_discipline.html', context)

@login_required
def manage_reward_discipline_record(request, pk=None):
    # ... (code manage_reward_discipline_record với redirect đã sửa) ...
    user = request.user
    # Chỉ cho phép nhân viên phòng giáo vụ (department_id=1) tạo/sửa
    can_manage = False
    if user.is_staff and hasattr(user, 'department') and user.department and user.department.id == 1:
        can_manage = True
    # Nếu là sửa (pk) thì vẫn cho phép admin/school_admin sửa (nếu cần, có thể giữ lại logic cũ cho admin)
    if pk and not can_manage:
        allowed_roles = ['SCHOOL_ADMIN', 'ADMIN']
        user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') else None
        if user.is_staff and user_role_name in allowed_roles:
            can_manage = True
    if not can_manage:
        raise PermissionDenied("Bạn không có quyền thực hiện hành động này. Chỉ nhân viên phòng Giáo vụ mới được phép.")

    instance = None
    if pk:
        instance = get_object_or_404(RewardAndDiscipline, pk=pk)

    if request.method == 'POST':
        form = RewardAndDisciplineForm(request.POST, instance=instance, requesting_user=user)
        if form.is_valid():
            new_record = form.save(commit=False)
            if not new_record.pk: 
                new_record.issued_by = user
            new_record.save()
            form.save_m2m()
            messages.success(request, f"Đã {'cập nhật' if pk else 'tạo mới'} mục khen thưởng/kỷ luật thành công.")

            # Gửi thông báo khi tạo mới
            if not pk:
                student = new_record.student
                student_user = student.user
                student_class = student.current_class
                # Lấy giáo viên chủ nhiệm
                homeroom_teacher = student_class.homeroom_teacher if student_class else None
                # Lấy phụ huynh
                parent_profile = getattr(student, 'parent', None)
                parent_user = parent_profile.user if parent_profile else None
                # Nội dung thông báo
                record_type_display = dict(RewardAndDiscipline.RECORD_TYPE_CHOICES).get(new_record.record_type, new_record.record_type)
                class_name = student_class.name if student_class else ""
                content = f"Nhà trường xin thông báo về quyết định {record_type_display} học sinh {student_user.get_full_name() or student_user.username} lớp {class_name}: {new_record.reason}"
                title = f"Quyết định {record_type_display} học sinh {student_user.get_full_name() or student_user.username}"
                notification = Notification.objects.create(
                    title=title,
                    content=content,
                    sent_by=user,
                    status='SENT',
                    is_published=True,
                    publish_time=timezone.now()
                )
                # Gửi cho học sinh
                notification.target_users.add(student_user)
                # Gửi cho giáo viên chủ nhiệm
                if homeroom_teacher:
                    notification.target_users.add(homeroom_teacher)
                # Gửi cho phụ huynh
                if parent_user:
                    notification.target_users.add(parent_user)

            return redirect('academic_records:school_wide_reward_discipline_list')
    else:
        form = RewardAndDisciplineForm(instance=instance, requesting_user=user)

    context = {
        'form': form,
        'page_title': f"{'Chỉnh sửa' if pk else 'Tạo mới'} Khen thưởng/Kỷ luật",
        'record_instance': instance
    }
    return render(request, 'academic_records/manage_reward_discipline_record.html', context)

@login_required
def teacher_view_class_rewards_discipline(request):
    # ... (code teacher_view_class_rewards_discipline không thay đổi) ...
    teacher = request.user
    if not (hasattr(teacher, 'role') and teacher.role and teacher.role.name == 'TEACHER'):
        raise PermissionDenied("Chức năng này chỉ dành cho Giáo viên.")

    homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=teacher)
    
    selected_class_pk_from_get = request.GET.get('class_to_view')
    active_class = None
    records_in_class = RewardAndDiscipline.objects.none()

    if selected_class_pk_from_get:
        active_class = get_object_or_404(SchoolClass, pk=selected_class_pk_from_get, homeroom_teacher=teacher)
    elif homeroom_classes.exists():
        active_class = homeroom_classes.first()

    if active_class:
        students_in_class_pks = StudentProfile.objects.filter(current_class=active_class).values_list('pk', flat=True)
        records_in_class = RewardAndDiscipline.objects.filter(student_id__in=students_in_class_pks).select_related('student__user', 'issued_by').order_by('-date_issued')
    else:
        if homeroom_classes.exists():
             messages.info(request, "Vui lòng chọn một lớp chủ nhiệm để xem.")
        else:
            messages.info(request, "Bạn hiện không chủ nhiệm lớp nào.")
            
    context = {
        'page_title': f'Khen thưởng/Kỷ luật Lớp {active_class.name}' if active_class else 'Khen thưởng/Kỷ luật Lớp Chủ Nhiệm',
        'active_class': active_class,
        'homeroom_classes': homeroom_classes,
        'records_in_class': records_in_class
    }
    return render(request, 'academic_records/teacher_view_class_rewards_discipline.html', context)

@login_required
def school_wide_reward_discipline_list(request):
    # ... (code school_wide_reward_discipline_list không thay đổi) ...
    user = request.user
    allowed_roles_for_school_wide_view = ['SCHOOL_ADMIN', 'ADMIN'] 
    
    can_view = False
    user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') else None

    if user_role_name in allowed_roles_for_school_wide_view and user.is_staff: # Thêm user.is_staff
        can_view = True
    elif user.is_staff and hasattr(user, 'department') and user.department:
        can_view = True
        
    if not can_view:
        raise PermissionDenied("Bạn không có quyền truy cập trang này.")

    all_records_qs = RewardAndDiscipline.objects.all().select_related(
        'student__user', 
        'student__current_class', 
        'issued_by'
    ).order_by('-date_issued', 'student__user__last_name')

    context = {
        'all_records': all_records_qs,
        'page_title': 'Tổng hợp Khen thưởng/Kỷ luật Toàn trường',
    }
    return render(request, 'academic_records/school_wide_reward_discipline_list.html', context)

# === VIEW MỚI CHO GIÁO VIÊN TẠO/SỬA ĐÁNH GIÁ ===
@login_required
def create_edit_evaluation(request, pk=None):
    user = request.user
    allowed_roles = ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN']
    user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') else None

    # Lấy loại đánh giá từ query param nếu có
    eval_type = request.GET.get('type')
    selected_class_id = request.GET.get('class_id')
    taught_classes = None
    if eval_type == 'SUBJECT_REVIEW' and hasattr(user, 'teacher_profile'):
        # Lấy các lớp mà giáo viên này giảng dạy (có học sinh học môn mà giáo viên này dạy)
        subjects_taught = user.teacher_profile.subjects_taught.all()
        taught_classes = SchoolClass.objects.filter(students__enrolled_subjects__in=subjects_taught).distinct().order_by('name')

    can_manage = False
    if user_role_name in allowed_roles and user.is_staff:
        can_manage = True
    if not can_manage:
        if not (user_role_name == 'TEACHER'):
            raise PermissionDenied("Bạn không có quyền thực hiện hành động này.")

    instance = None
    if pk:
        instance = get_object_or_404(Evaluation, pk=pk)
        if instance.evaluator != user and not (user_role_name in ['SCHOOL_ADMIN', 'ADMIN'] and user.is_staff):
            raise PermissionDenied("Bạn không có quyền sửa đánh giá này.")

    # Xử lý POST
    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=instance, requesting_user=user, eval_type=eval_type, selected_class_id=selected_class_id)
        if form.is_valid():
            evaluation = form.save(commit=False)
            is_new = not evaluation.pk
            if is_new:
                evaluation.evaluator = user
            evaluation.evaluation_date = timezone.now()
            evaluation.save()
            form.save_m2m()
            messages.success(request, f"Đã {'cập nhật' if pk else 'tạo mới'} đánh giá/nhận xét thành công.")
            # Gửi thông báo khi tạo mới (giữ nguyên như trước)
            if is_new:
                student = evaluation.student
                student_user = student.user
                parent_profile = getattr(student, 'parent', None)
                parent_user = parent_profile.user if parent_profile else None
                eval_type_display = evaluation.get_evaluation_type_display()
                subject_name = evaluation.subject.name if evaluation.subject else ""
                if evaluation.evaluation_type == 'SUBJECT_REVIEW':
                    content = f"Nhà trường xin thông báo về nhận xét môn học {subject_name} cho học sinh {student_user.get_full_name() or student_user.username}: {evaluation.content}"
                    title = f"Nhận xét môn {subject_name} cho học sinh {student_user.get_full_name() or student_user.username}"
                else:
                    content = f"Nhà trường xin thông báo về đánh giá {eval_type_display} của học sinh {student_user.get_full_name() or student_user.username}: {evaluation.content}"
                    title = f"Đánh giá {eval_type_display} cho học sinh {student_user.get_full_name() or student_user.username}"
                notification = Notification.objects.create(
                    title=title,
                    content=content,
                    sent_by=user,
                    status='SENT',
                    is_published=True,
                    publish_time=timezone.now()
                )
                notification.target_users.add(student_user)
                if parent_user:
                    notification.target_users.add(parent_user)
            if evaluation.student:
                pass
            return redirect('homepage')
    else:
        form = EvaluationForm(instance=instance, requesting_user=user, eval_type=eval_type, selected_class_id=selected_class_id)

    context = {
        'form': form,
        'page_title': f"{'Chỉnh sửa' if pk else 'Tạo mới'} Đánh giá/Nhận xét",
        'evaluation_instance': instance,
        'eval_type': eval_type,
        'taught_classes': taught_classes,
        'selected_class_id': selected_class_id,
    }
    return render(request, 'academic_records/create_edit_evaluation.html', context)

@login_required
def view_evaluations(request):
    user = request.user
    context = {
        'page_title': 'Đánh giá và Nhận xét',
        'evaluations_conduct_by_student': defaultdict(list),
        'evaluations_subject_review_by_student': defaultdict(list),
        'is_parent': False,
        'students_to_view': [],
        'error_message': None
    }

    user_role_name = getattr(user.role, 'name', None) if hasattr(user, 'role') and user.role else None

    if user_role_name == 'STUDENT':
        try:
            student_profile = StudentProfile.objects.get(user=user) 
            context['students_to_view'] = [student_profile]
            context['page_title'] = f'Đánh giá/Nhận xét cho {student_profile.user.get_full_name() or student_profile.user.username}'
        except StudentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ học sinh của bạn."
    elif user_role_name == 'PARENT':
        context['is_parent'] = True
        try:
            parent_profile = ParentProfile.objects.get(user=user)
            children_profiles_qs = parent_profile.children.all().select_related('user')
            if not children_profiles_qs.exists():
                context['error_message'] = "Bạn chưa có thông tin học sinh nào được liên kết."
            else:
                context['students_to_view'] = list(children_profiles_qs)
                context['page_title'] = 'Đánh giá/Nhận xét của các con'
        except ParentProfile.DoesNotExist:
            context['error_message'] = "Không tìm thấy hồ sơ phụ huynh của bạn."
        except Exception as e: 
            context['error_message'] = "Đã có lỗi xảy ra khi truy xuất thông tin phụ huynh."
    else:
        context['error_message'] = "Chức năng này chỉ dành cho Học sinh và Phụ huynh."

    if context['students_to_view']:
        student_pks = [sp.pk for sp in context['students_to_view']]
        evaluations_qs = Evaluation.objects.filter(
            student_id__in=student_pks
        ).select_related('student__user', 'evaluator', 'subject').order_by('student__user__username', '-evaluation_date')
        for evaluation_item in evaluations_qs:
            student_display_name = evaluation_item.student.user.get_full_name() or evaluation_item.student.user.username
            if evaluation_item.evaluation_type in ['CONDUCT', 'TERM_REVIEW']:
                context['evaluations_conduct_by_student'][student_display_name].append(evaluation_item)
            elif evaluation_item.evaluation_type == 'SUBJECT_REVIEW':
                context['evaluations_subject_review_by_student'][student_display_name].append(evaluation_item)
    # Chuyển defaultdict thành dict thường
    context['evaluations_conduct_by_student'] = dict(context['evaluations_conduct_by_student'])
    context['evaluations_subject_review_by_student'] = dict(context['evaluations_subject_review_by_student'])
    return render(request, 'academic_records/view_evaluations.html', context)

@login_required
def teacher_my_evaluations(request):
    user = request.user
    # Kiểm tra quyền: Chỉ Giáo viên
    if not (hasattr(user, 'role') and user.role and user.role.name == 'TEACHER'):
        raise PermissionDenied("Chức năng này chỉ dành cho Giáo viên.")

    # Lấy tất cả các đánh giá mà giáo viên này đã tạo
    my_evaluations = Evaluation.objects.filter(
        evaluator=user
    ).select_related('student__user', 'subject').order_by('-evaluation_date', 'student__user__last_name')

    # Phân loại
    evaluations_conduct = [e for e in my_evaluations if e.evaluation_type in ['CONDUCT', 'TERM_REVIEW']]
    evaluations_subject_review = [e for e in my_evaluations if e.evaluation_type == 'SUBJECT_REVIEW']

    # Kiểm tra giáo viên có chủ nhiệm lớp nào không
    homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=user)
    is_homeroom_teacher = homeroom_classes.exists()

    context = {
        'evaluations_conduct': evaluations_conduct,
        'evaluations_subject_review': evaluations_subject_review,
        'is_homeroom_teacher': is_homeroom_teacher,
        'page_title': 'Đánh giá học sinh & Nhận xét môn học',
    }
    return render(request, 'academic_records/teacher_my_evaluations.html', context)

@login_required
def manage_scores_dashboard(request):
    teacher = request.user
    if not (hasattr(teacher, 'role') and teacher.role and teacher.role.name == 'TEACHER'):
        raise PermissionDenied("Chức năng này chỉ dành cho Giáo viên.")

    # Define the desired order of exam types
    exam_type_order_keys = [
        'ORAL_TEST', '15_MIN_TEST', '45_MIN_TEST',
        'MID_TERM_1', 'END_TERM_1',
        'MID_TERM_2', 'END_TERM_2',
        'FINAL_EXAM'
    ]
    exam_type_when_conditions = []
    for i, exam_type_key in enumerate(exam_type_order_keys):
        exam_type_when_conditions.append(When(exam_type=exam_type_key, then=Value(i)))

    context = {
        'page_title': 'Quản lý Điểm',
        'homeroom_classes_list': [],
        'active_homeroom_class': None,
        'homeroom_data': defaultdict(lambda: {
            'teacher_name_display': "N/A", # Default
            'students_map': defaultdict(lambda: {'scores': [], 'student_info': None})
        }),
        'taught_classes_data': defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'scores': [], 'student_info': None}))),
        'all_score_types_choices': Score.EXAM_TYPE_CHOICES,
    }

    # 1. Homeroom Class Data
    homeroom_classes = SchoolClass.objects.filter(homeroom_teacher=teacher).order_by('name')
    context['homeroom_classes_list'] = homeroom_classes
    
    selected_hr_class_pk = request.GET.get('homeroom_class_pk')
    active_homeroom_class = None
    if selected_hr_class_pk:
        active_homeroom_class = get_object_or_404(SchoolClass, pk=selected_hr_class_pk, homeroom_teacher=teacher)
    elif homeroom_classes.exists():
        active_homeroom_class = homeroom_classes.first()
    context['active_homeroom_class'] = active_homeroom_class

    if active_homeroom_class:
        students_in_hr = StudentProfile.objects.filter(current_class=active_homeroom_class).select_related('user').order_by('user__last_name', 'user__first_name')
        all_subjects_for_hr_view = SchoolSubject.objects.all().order_by('name').prefetch_related('teachers__user') # User's preference

        homeroom_teacher_user = active_homeroom_class.homeroom_teacher
        homeroom_teacher_profile = None
        if homeroom_teacher_user:
            homeroom_teacher_profile = getattr(homeroom_teacher_user, 'teacher_profile', None)

        for subj in all_subjects_for_hr_view: # Iterate over all subjects
            display_teacher_names = []
            # Check if homeroom teacher teaches this subject
            if homeroom_teacher_profile and subj in homeroom_teacher_profile.subjects_taught.all():
                display_teacher_names.append(homeroom_teacher_user.get_full_name() or homeroom_teacher_user.username)
            else:
                # If not taught by homeroom teacher, list other general teachers of the subject
                for teacher_profile_obj in subj.teachers.all(): # These are TeacherProfile instances
                    teacher_user = teacher_profile_obj.user
                    teacher_name = teacher_user.get_full_name() or teacher_user.username
                    display_teacher_names.append(teacher_name)
            
            # Use set to ensure unique names if a teacher falls into multiple categories (unlikely here but good practice)
            unique_display_teacher_names = sorted(list(set(display_teacher_names)))
            teacher_name_str = ", ".join(unique_display_teacher_names) if unique_display_teacher_names else "N/A"
            
            context['homeroom_data'][subj]['teacher_name_display'] = teacher_name_str
            
            for stud_profile in students_in_hr:
                if not context['homeroom_data'][subj]['students_map'][stud_profile.pk]['student_info']:
                    context['homeroom_data'][subj]['students_map'][stud_profile.pk]['student_info'] = stud_profile
                
                scores = (Score.objects.filter(student=stud_profile, subject=subj)
                    .annotate(
                        custom_exam_type_order=Case(
                            *exam_type_when_conditions,
                            default=Value(len(exam_type_order_keys)),
                            output_field=IntegerField()
                        )
                    )
                    .order_by('exam_date', 'custom_exam_type_order', 'exam_type'))
                context['homeroom_data'][subj]['students_map'][stud_profile.pk]['scores'] = list(scores)

    # 2. Taught Classes Data (không dùng teachers field)
    teacher_profile_obj = getattr(teacher, 'teacher_profile', None)
    subjects_personally_taught = teacher_profile_obj.subjects_taught.all().order_by('name') if teacher_profile_obj else SchoolSubject.objects.none()
    # Lấy tất cả các lớp có học sinh học môn mà giáo viên này dạy, loại trừ lớp chủ nhiệm
    taught_classes_qs = SchoolClass.objects.filter(
        students__enrolled_subjects__in=subjects_personally_taught
    ).exclude(homeroom_teacher=teacher).distinct().order_by('name')
    for t_class in taught_classes_qs:
        students_in_t_class = StudentProfile.objects.filter(current_class=t_class).select_related('user').order_by('user__last_name', 'user__first_name')
        for subj_taught in subjects_personally_taught:
            for stud_profile in students_in_t_class:
                if not context['taught_classes_data'][t_class][subj_taught][stud_profile.pk]['student_info']:
                    context['taught_classes_data'][t_class][subj_taught][stud_profile.pk]['student_info'] = stud_profile
                scores = (Score.objects.filter(student=stud_profile, subject=subj_taught)
                    .annotate(
                        custom_exam_type_order=Case(
                            *exam_type_when_conditions,
                            default=Value(len(exam_type_order_keys)),
                            output_field=IntegerField()
                        )
                    )
                    .order_by('exam_date', 'custom_exam_type_order', 'exam_type'))
                context['taught_classes_data'][t_class][subj_taught][stud_profile.pk]['scores'] = list(scores)

    # Chuyển defaultdict thành dict thường để template dễ xử lý hơn
    final_homeroom_data = {}
    for subj_obj, data_dict in context['homeroom_data'].items():
       final_homeroom_data[subj_obj] = {
           'teacher_name_display': data_dict['teacher_name_display'],
           'students_map': dict(data_dict['students_map']) # Convert inner defaultdict
       }
       # Ensure students_map's inner dicts are also plain dicts if necessary (they are already {'scores': [], 'student_info': None})
       for student_pk, student_data in final_homeroom_data[subj_obj]['students_map'].items():
           final_homeroom_data[subj_obj]['students_map'][student_pk] = dict(student_data)

    context['homeroom_data'] = final_homeroom_data

    final_taught_classes_data = {}
    for class_obj, subject_map in context['taught_classes_data'].items():
        final_taught_classes_data[class_obj] = {}
        for subj, student_map_val in subject_map.items():
            if any(s_data['scores'] or s_data['student_info'] for s_data in student_map_val.values()):
                final_taught_classes_data[class_obj][subj] = dict(student_map_val)
        if not final_taught_classes_data[class_obj]:
            del final_taught_classes_data[class_obj]
    context['taught_classes_data'] = final_taught_classes_data
    return render(request, 'academic_records/teacher_view_class_scores.html', context)

@login_required
def school_wide_evaluations(request):
    user = request.user
    if not (user.is_staff and hasattr(user, 'department') and user.department):
        raise PermissionDenied("Bạn không có quyền truy cập trang này.")
    evaluations_conduct = Evaluation.objects.filter(
        evaluation_type__in=['CONDUCT', 'TERM_REVIEW']
    ).select_related('student__user', 'student__current_class', 'evaluator').order_by('-evaluation_date')
    evaluations_subject_review = Evaluation.objects.filter(
        evaluation_type='SUBJECT_REVIEW'
    ).select_related('student__user', 'student__current_class', 'subject', 'evaluator').order_by('-evaluation_date')
    context = {
        'evaluations_conduct': evaluations_conduct,
        'evaluations_subject_review': evaluations_subject_review,
        'page_title': 'Tổng hợp Đánh giá & Nhận xét Toàn trường',
    }
    return render(request, 'academic_records/school_wide_evaluations.html', context)

@login_required
def school_wide_scores(request):
    user = request.user
    if not (user.is_staff and hasattr(user, 'department') and user.department):
        raise PermissionDenied("Bạn không có quyền truy cập trang này.")
    all_classes = SchoolClass.objects.all().order_by('name')
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students_in_class = []
    scores_by_subject = {}
    if selected_class_id:
        try:
            selected_class = SchoolClass.objects.get(pk=selected_class_id)
            students_in_class = StudentProfile.objects.filter(current_class=selected_class).select_related('user').order_by('user__last_name', 'user__first_name')
            subjects = SchoolSubject.objects.all().order_by('name').prefetch_related('teachers__user')
            for subject in subjects:
                subject_scores = []
                # Lấy giáo viên thực sự dạy môn này cho lớp này
                teacher_names = []
                for teacher_profile in subject.teachers.all():
                    if hasattr(teacher_profile, 'subjects_taught') and subject in teacher_profile.subjects_taught.all():
                        teacher_names.append(teacher_profile.user.get_full_name() or teacher_profile.user.username)
                teacher_names_str = ", ".join(sorted(list(set(teacher_names)))) or "N/A"
                subject.teacher_names = teacher_names_str
                for student in students_in_class:
                    scores = Score.objects.filter(student=student, subject=subject).order_by('exam_date', 'exam_type')
                    subject_scores.append({
                        'student': student,
                        'scores': list(scores)
                    })
                scores_by_subject[subject] = subject_scores
        except SchoolClass.DoesNotExist:
            selected_class = None
    context = {
        'page_title': 'Tổng hợp điểm theo lớp',
        'all_classes': all_classes,
        'selected_class': selected_class,
        'scores_by_subject': scores_by_subject,
        'students_in_class': students_in_class,
    }
    return render(request, 'academic_records/school_wide_scores.html', context)
