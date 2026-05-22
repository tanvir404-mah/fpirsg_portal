from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
import json

BLOOD_GROUP_CHOICES = (
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
)

DEPARTMENT_CHOICES = (
    ('CST', 'Computer Science & Technology'),
    ('Civil', 'Civil Engineering'),
    ('Electrical', 'Electrical Engineering'),
    ('Mechanical', 'Mechanical Engineering'),
    ('Power', 'Power Engineering'),
    ('Electronics', 'Electronics Engineering'),
    ('Architecture', 'Architecture'),
    ('RAC', 'RAC'),
)

SEMESTER_CHOICES = (
    ('1st', '1st Semester'),
    ('2nd', '2nd Semester'),
    ('3rd', '3rd Semester'),
    ('4th', '4th Semester'),
    ('5th', '5th Semester'),
    ('6th', '6th Semester'),
    ('7th', '7th Semester'),
    ('8th', '8th Semester'),
)

SHIFT_CHOICES = (
    ('1st', '1st Shift'),
    ('2nd', '2nd Shift'),
)

class RoverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rover_profile')
    form_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    
    # Personal Info
    name_en = models.CharField(max_length=150, verbose_name="Name (English)")
    name_bn = models.CharField(max_length=150, verbose_name="Name (Bangla)")
    father_name_en = models.CharField(max_length=150, verbose_name="Father's Name (English)")
    father_name_bn = models.CharField(max_length=150, verbose_name="Father's Name (Bangla)")
    mother_name_en = models.CharField(max_length=150, verbose_name="Mother's Name (English)")
    mother_name_bn = models.CharField(max_length=150, verbose_name="Mother's Name (Bangla)")
    dob = models.DateField(verbose_name="Date of Birth")
    religion = models.CharField(max_length=50)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    
    # Contact Info
    mobile = models.CharField(max_length=15)
    guardian_mobile = models.CharField(max_length=15)
    email = models.EmailField()
    
    # Addresses
    present_address = models.JSONField(default=dict, help_text="Format: {'village': '', 'post_office': '', 'post_code': '', 'upazila': '', 'district': '', 'division': ''}")
    permanent_address = models.JSONField(default=dict, help_text="Format: {'village': '', 'post_office': '', 'post_code': '', 'upazila': '', 'district': '', 'division': ''}")
    
    # Academic Info
    ssc_year = models.IntegerField(verbose_name="SSC Passing Year")
    ssc_gpa = models.FloatField(verbose_name="SSC GPA")
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    session = models.CharField(max_length=20, help_text="e.g., 2023-24")
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    roll_no = models.CharField(max_length=20, unique=True, verbose_name="Polytechnic Roll No")
    
    # Experience & Skills
    cub_experience = models.BooleanField(default=False)
    cub_badge = models.CharField(max_length=100, blank=True, null=True)
    scout_experience = models.BooleanField(default=False)
    scout_badge = models.CharField(max_length=100, blank=True, null=True)
    other_skills = models.TextField(blank=True, null=True)
    
    profile_pic = models.ImageField(upload_to='profile_pics/')
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name_en} - {self.roll_no}"

@receiver(pre_save, sender=RoverProfile)
def generate_form_number(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = RoverProfile.objects.get(pk=instance.pk)
            if instance.is_approved and not old_instance.is_approved and not instance.form_number:
                count = RoverProfile.objects.filter(
                    session=instance.session,
                    is_approved=True
                ).count()
                
                next_serial = count + 1
                formatted_serial = f"{next_serial:03d}"
                instance.form_number = f"FPIRSG-{instance.session}-{formatted_serial}"
        except RoverProfile.DoesNotExist:
            pass

class Notice(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class FeeStructure(models.Model):
    FREQUENCY_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fee Amount (BDT)")
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='MONTHLY')
    description = models.CharField(max_length=255, blank=True, help_text="e.g., Monthly Rover Fund, Weekly Dues")
    is_active = models.BooleanField(default=True, help_text="Enable/disable fee collection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Fee Structures"
    
    def __str__(self):
        return f"Fee: ৳{self.amount} ({self.get_frequency_display()})"

class RoverFee(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    )
    
    FREQUENCY_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    )
    
    rover = models.ForeignKey(RoverProfile, on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.rover.name_en} - ৳{self.amount} ({self.status})"

class FundTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Income / Collection'),
        ('OUT', 'Expense'),
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES, default='IN')
    description = models.CharField(max_length=255)
    date = models.DateField()
    rover = models.ForeignKey(RoverProfile, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: If collected from a specific Rover")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} BDT on {self.date}"

@receiver(post_save, sender=RoverProfile)
def create_initial_fee_on_approval(sender, instance, created, **kwargs):
    """Auto-create first pending fee when rover is approved"""
    if instance.is_approved:
        try:
            fee_structure = FeeStructure.objects.filter(is_active=True).first()
            if fee_structure:
                # Check if rover already has a pending fee
                existing_pending = RoverFee.objects.filter(rover=instance, status='PENDING').exists()
                if not existing_pending:
                    # Calculate due date
                    today = datetime.now().date()
                    if fee_structure.frequency == 'WEEKLY':
                        due_date = today + timedelta(days=7)
                    else:  # MONTHLY
                        due_date = today + timedelta(days=30)
                    
                    RoverFee.objects.create(
                        rover=instance,
                        amount=fee_structure.amount,
                        frequency=fee_structure.frequency,
                        status='PENDING',
                        due_date=due_date
                    )
        except FeeStructure.DoesNotExist:
            pass
