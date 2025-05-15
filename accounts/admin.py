from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Đổi tên để tránh xung đột
from .models import User, Role, TeacherProfile, StudentProfile, ParentProfile

# --- Admin cho các Model riêng lẻ (nếu cần cho raw_id_fields hoặc quản lý riêng) ---
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display_custom', 'description')
    search_fields = ('name', 'description')

    def get_name_display_custom(self, obj):
        return obj.get_name_display()
    get_name_display_custom.short_description = 'Tên Vai trò Hiển thị'
    get_name_display_custom.admin_order_field = 'name'

@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'address')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'address')
    autocomplete_fields = ['user'] # Giúp chọn User cho ParentProfile

    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() if obj.user.get_full_name() else obj.user.username
        return "-"
    user_display.short_description = "Tài khoản Phụ huynh"
    user_display.admin_order_field = 'user__username'

@admin.register(StudentProfile) # Đăng ký StudentProfile riêng để raw_id_fields/autocomplete hoạt động tốt
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'date_of_birth', 'gender', 'current_class_name', 'parent_full_name')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'current_class__name'
    )
    list_filter = ('gender', 'current_class')
    autocomplete_fields = ['user', 'current_class', 'parent']
    filter_horizontal = ('enrolled_subjects',) # Quản lý môn học đã đăng ký

    def user_display(self, obj):
        return obj.user.get_full_name() if obj.user.get_full_name() else obj.user.username
    user_display.short_description = 'Học sinh'
    user_display.admin_order_field = 'user__last_name'

    def current_class_name(self, obj):
        return obj.current_class.name if obj.current_class else '-'
    current_class_name.short_description = 'Lớp Hiện Tại'

    def parent_full_name(self, obj):
        if obj.parent and obj.parent.user:
            return obj.parent.user.get_full_name() if obj.parent.user.get_full_name() else obj.parent.user.username
        return '-'
    parent_full_name.short_description = 'Phụ Huynh Chính'


# --- Inlines cho User Admin ---
class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ Giáo viên'
    fk_name = 'user'
    fieldsets = (
        (None, {'fields': ('teacher_type',)}),
        ('Các môn học giảng dạy', {'fields': ('subjects_taught',)}),
    )
    filter_horizontal = ('subjects_taught',)
    # raw_id_fields = ('user',) # Không cần thiết vì đây là inline của User

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ Học sinh'
    fk_name = 'user'
    fieldsets = (
        (None, {'fields': ('date_of_birth', 'gender')}),
        ('Thông tin Học Tập và Gia Đình', {
            'fields': ('current_class', 'parent', 'enrolled_subjects') # Đã có enrolled_subjects
        }),
    )
    filter_horizontal = ('enrolled_subjects',) # Đã có
    raw_id_fields = ('current_class', 'parent') # Giữ nguyên nếu hoạt động tốt

class ParentProfileInline(admin.StackedInline):
    model = ParentProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ Phụ huynh'
    fk_name = 'user'
    fields = ('address',) # Chỉ có trường address

# --- Custom User Admin ---
@admin.register(User) # Sử dụng decorator để đăng ký User với CustomUserAdmin
class CustomUserAdmin(BaseUserAdmin): # Kế thừa từ BaseUserAdmin
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role_display', 'department_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Thông tin Mở rộng & Vai trò', {'fields': ('role', 'department')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Thông tin Mở rộng & Vai trò', {'fields': ('role', 'department')}),
    )
    inlines = (TeacherProfileInline, StudentProfileInline, ParentProfileInline,)
    list_filter = BaseUserAdmin.list_filter + ('department', 'role')
    search_fields = BaseUserAdmin.search_fields + ('department__name', 'role__name')
    autocomplete_fields = ['department', 'role'] # 'groups' đã có trong BaseUserAdmin

    def department_name(self, obj):
        if obj.department:
            return obj.department.name
        return "-"
    department_name.short_description = 'Phòng Ban'
    department_name.admin_order_field = 'department__name'

    def role_display(self, obj):
        if obj.role:
            return obj.role.get_name_display() # Sử dụng get_name_display cho Role
        return "-"
    role_display.short_description = 'Vai trò'
    role_display.admin_order_field = 'role__name'
