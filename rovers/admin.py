from django.contrib import admin
from .models import RoverProfile, Notice, FundTransaction, FeeStructure, RoverFee

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('amount', 'frequency', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('frequency', 'is_active')
    search_fields = ('amount',)

@admin.register(RoverFee)
class RoverFeeAdmin(admin.ModelAdmin):
    list_display = ('rover', 'amount', 'frequency', 'status', 'due_date')
    list_filter = ('status', 'frequency')
    search_fields = ('rover__name_en', 'rover__roll_no')


@admin.register(RoverProfile)
class RoverProfileAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'roll_no', 'department', 'session', 'blood_group', 'form_number', 'is_approved')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'blood_group', 'department', 'session')
    search_fields = ('name_en', 'name_bn', 'roll_no', 'form_number', 'mobile', 'email')
    readonly_fields = ('form_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'form_number', 'is_approved')
        }),
        ('Personal Information', {
            'fields': ('name_en', 'name_bn', 'father_name_en', 'father_name_bn', 'mother_name_en', 'mother_name_bn', 'dob', 'religion', 'blood_group')
        }),
        ('Contact Information', {
            'fields': ('mobile', 'guardian_mobile', 'email', 'present_address', 'permanent_address')
        }),
        ('Academic Information', {
            'fields': ('ssc_year', 'ssc_gpa', 'department', 'session', 'semester', 'shift', 'roll_no')
        }),
        ('Experience & Skills', {
            'fields': ('cub_experience', 'cub_badge', 'scout_experience', 'scout_badge', 'other_skills')
        }),
        ('Profile Picture & Meta', {
            'fields': ('profile_pic', 'created_at', 'updated_at')
        }),
    )

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content')

@admin.register(FundTransaction)
class FundTransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'transaction_type', 'date', 'rover')
    list_filter = ('transaction_type', 'date')
    search_fields = ('description', 'rover__name_en', 'rover__roll_no')
