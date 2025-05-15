from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Tên Phòng Ban")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Email Phòng Ban")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Phòng Ban"
        verbose_name_plural = "Các Phòng Ban"

class Class(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên Lớp học")
    homeroom_teacher = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeroom_classes',
        verbose_name="Giáo viên Chủ nhiệm",
        limit_choices_to={'role__name': 'TEACHER'} 
    )
    academic_year = models.CharField(max_length=9, blank=True, null=True, verbose_name="Năm học (VD: 2024-2025)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lớp học"
        verbose_name_plural = "Các Lớp học"
        unique_together = ('name', 'academic_year') # Đảm bảo tên lớp là duy nhất trong một năm học

class Subject(models.Model):
    # ERD: subject_id (PK - Django tự tạo), name
    name = models.CharField(max_length=150, unique=True, verbose_name="Tên Môn học")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả Môn học")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Môn học"
        verbose_name_plural = "Các Môn học"