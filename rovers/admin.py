from django.contrib import admin
from .models import RoverProfile, Notice, FundTransaction, FeeStructure, RoverFee, LeaderBoard, RoverRank, RoverStage

# ==================== FEE STRUCTURE & FEES ====================
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


# ==================== ROVER MASTER RANKS & STAGES ====================
admin.site.register(RoverRank)
admin.site.register(RoverStage)


# ==================== ROVER PROFILE ADMIN (UPDATED) ====================
@admin.register(RoverProfile)
class RoverProfileAdmin(admin.ModelAdmin):
    # লিস্ট ভিউতে র‍্যাংক এবং স্টেজ কলাম যুক্ত করা হলো
    list_display = ('name_en', 'roll_no', 'department', 'session', 'rank', 'stage', 'is_approved')
    list_editable = ('is_approved',)
    # ফিল্টার প্যানেলে র‍্যাংক এবং স্টেজ যোগ করা হলো
    list_filter = ('is_approved', 'rank', 'stage', 'blood_group', 'department', 'session')
    search_fields = ('name_en', 'name_bn', 'roll_no', 'form_number', 'mobile', 'email')
    readonly_fields = ('form_number', 'created_at', 'updated_at')
    
    # আপনার আগের সব ফিল্ডের সাথে স্কাউট আইডি ও র‍্যাংক ম্যানেজমেন্ট যোগ করা হলো
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'form_number', 'is_approved')
        }),
        ('Scout Rank & Stage (নতুন)', {
            'fields': ('rank', 'stage') # প্রোফাইলের ভেতরে এই ড্রপডাউন দুটি শো করবে
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


# ==================== NOTICES & FUND TRANSACTIONS ====================
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


# ==================== LEADERSHIP BOARD (GP, GS, RSL, SRM) ====================
class LeaderBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'phone', 'email', 'order')
    list_filter = ('role',)
    search_fields = ('name', 'phone', 'email')
    list_editable = ('order',)

admin.site.register(LeaderBoard, LeaderBoardAdmin)