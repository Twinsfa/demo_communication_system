from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Quản trị viên Hệ thống (Admin)'), # Phòng CNTT
        ('SCHOOL_ADMIN', 'Quản lý Trường (Phòng Ban khác)'),
        ('TEACHER', 'Giáo viên'),
        ('PARENT', 'Phụ huynh'),
        ('STUDENT', 'Học sinh'),
    ]
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True, primary_key=True) # Đặt name làm PK và unique
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả vai trò")

    def __str__(self):
        return self.get_name_display() # Hiển thị tên đầy đủ của choice

class User(AbstractUser):

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vai trò")

    department = models.ForeignKey(
        'school_data.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Không phải tất cả user đều thuộc về một phòng ban (VD: Học sinh, Phụ huynh)
        related_name='staff_members', # Từ Department, có thể truy cập ds nhân viên: phong_ban.staff_members.all()
        verbose_name="Phòng Ban Công tác (nếu có)"
    )


    def __str__(self):
        return self.username
    

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    TEACHER_TYPE_CHOICES = [
        ('HEAD_TEACHER', 'Giáo viên Chủ nhiệm'),
        ('SUBJECT_TEACHER', 'Giáo viên Bộ môn'),
        ('STAFF', 'Nhân viên Phòng Ban'),
    ]
    teacher_type = models.CharField(max_length=20, choices=TEACHER_TYPE_CHOICES, null=True, blank=True, verbose_name="Loại giáo viên/nhân viên")

    # --- THÊM TRƯỜNG MỚI Ở ĐÂY ---
    subjects_taught = models.ManyToManyField(
        'school_data.Subject', # Sử dụng string 'app_name.ModelName'
        blank=True, # Giáo viên có thể (tạm thời) chưa được phân công dạy môn nào
        related_name='teachers', # Từ một Subject, có thể truy cập ds giáo viên: mon_hoc.teachers.all()
        verbose_name="Các Môn học Giảng dạy"
    )
    # --- KẾT THÚC PHẦN THÊM MỚI ---

    def __str__(self):
        # Hiển thị tên các môn học nếu có
        subject_names = ", ".join([subject.name for subject in self.subjects_taught.all()])
        if subject_names:
            return f"GV: {self.user.username} (Dạy: {subject_names})"
        return f"GV: {self.user.username}"

# ... (các model StudentProfile, ParentProfile đã có ở dưới) ...
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    GENDER_CHOICES = [
        ('MALE', 'Nam'),
        ('FEMALE', 'Nữ'),
        ('OTHER', 'Khác'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Giới tính")
    current_class = models.ForeignKey(
        'school_data.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Lớp Hiện Tại"
    )
    parent = models.ForeignKey(
        'ParentProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Phụ Huynh Chính"
    )

    # --- THÊM TRƯỜNG MỚI Ở ĐÂY ---
    enrolled_subjects = models.ManyToManyField(
        'school_data.Subject',
        blank=True, # Học sinh có thể (tạm thời) chưa đăng ký môn nào
        related_name='enrolled_students', # Từ một Subject, có thể truy cập ds học sinh: mon_hoc.enrolled_students.all()
        verbose_name="Các Môn học Đã đăng ký/Học"
    )


    def __str__(self):
        return f"Hồ sơ Học sinh: {self.user.username}"

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='parent_profile')
    # ERD: address
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")

    def __str__(self):
        return f"Hồ sơ Phụ huynh: {self.user.username}"