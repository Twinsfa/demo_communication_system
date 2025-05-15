from django.contrib import admin
from .models import Department, Class, Subject

# Đăng ký model Department
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'description') # Các trường hiển thị trong danh sách
    search_fields = ('name', 'email') # Cho phép tìm kiếm theo tên và email

# Đăng ký model Class
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'homeroom_teacher', 'academic_year') # Các trường hiển thị
    search_fields = ('name', 'academic_year') # Tìm kiếm theo tên lớp, năm học
    list_filter = ('academic_year', 'homeroom_teacher') 
    autocomplete_fields = ['homeroom_teacher']

# Đăng ký model Subject
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description') # Các trường hiển thị
    search_fields = ('name',) 