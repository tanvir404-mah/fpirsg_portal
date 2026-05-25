from django import forms
from django.contrib.auth.models import User
from .models import RoverProfile, Notice, FundTransaction, FeeStructure, RoverFee

INPUT_CLASS = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white transition'
SELECT_CLASS = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white transition'
TEXTAREA_CLASS = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white transition'
CHECKBOX_CLASS = 'w-5 h-5 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600'


class RoverRegistrationForm(forms.ModelForm):
    # Auth fields
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Enter password'}),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Confirm password'}),
        label='Confirm Password'
    )

    # Address fields as plain text (will be converted to JSON on save)
    present_village    = forms.CharField(max_length=100, required=False, label='Village/Area')
    present_post       = forms.CharField(max_length=100, required=False, label='Post Office')
    present_post_code  = forms.CharField(max_length=20,  required=False, label='Post Code')
    present_upazila    = forms.CharField(max_length=100, required=False, label='Upazila')
    present_district   = forms.CharField(max_length=100, required=True,  label='District')
    present_division   = forms.CharField(max_length=100, required=False, label='Division')

    permanent_village   = forms.CharField(max_length=100, required=False, label='Village/Area')
    permanent_post      = forms.CharField(max_length=100, required=False, label='Post Office')
    permanent_post_code = forms.CharField(max_length=20,  required=False, label='Post Code')
    permanent_upazila   = forms.CharField(max_length=100, required=False, label='Upazila')
    permanent_district  = forms.CharField(max_length=100, required=True,  label='District')
    permanent_division  = forms.CharField(max_length=100, required=False, label='Division')

    class Meta:
        model = RoverProfile
        exclude = ('user', 'form_number', 'is_approved', 'present_address', 'permanent_address')
        fields = '__all__'
        widgets = {
            'name_en':         forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Full name in English'}),
            'name_bn':         forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'পূর্ণ নাম বাংলায়'}),
            'father_name_en':  forms.TextInput(attrs={'class': INPUT_CLASS}),
            'father_name_bn':  forms.TextInput(attrs={'class': INPUT_CLASS}),
            'mother_name_en':  forms.TextInput(attrs={'class': INPUT_CLASS}),
            'mother_name_bn':  forms.TextInput(attrs={'class': INPUT_CLASS}),
            'dob':             forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'religion':        forms.TextInput(attrs={'class': INPUT_CLASS}),
            'blood_group':     forms.Select(attrs={'class': SELECT_CLASS}),
            'mobile':          forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '01XXXXXXXXX'}),
            'guardian_mobile': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '01XXXXXXXXX'}),
            'email':           forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'ssc_year':        forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'ssc_gpa':         forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'department':      forms.Select(attrs={'class': SELECT_CLASS}),
            # 'session' widget সরিয়ে দেওয়া হয়েছে এখান থেকে যেন এটি ড্রপডাউন ফিল্ড হয়
            'semester':        forms.Select(attrs={'class': SELECT_CLASS}),
            'shift':           forms.Select(attrs={'class': SELECT_CLASS}),
            'roll_no':         forms.TextInput(attrs={'class': INPUT_CLASS}),
            'cub_badge':       forms.TextInput(attrs={'class': INPUT_CLASS}),
            'scout_badge':     forms.TextInput(attrs={'class': INPUT_CLASS}),
            'other_skills':    forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'cub_experience':  forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'scout_experience':forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'profile_pic':     forms.FileInput(attrs={'class': 'hidden', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ১. সেশন ফিল্ডকে কাস্টম ড্রপডাউনে রূপান্তর (কোনো ডিফল্ট ভ্যালু ছাড়া)
        SESSION_CHOICES = [
            ('', '-- Select Session --'),  # প্রথম অপশন খালি, ইউজারকে সিলেক্ট করতে বাধ্য করবে
            ('2022-23', '2022-23'),
            ('2023-24', '2023-24'),
            ('2024-25', '2024-25'),
            ('2025-26', '2025-26'),
            ('2026-27', '2026-27'),
            ('2027-28', '2027-28'),
            ('2028-29', '2028-29'),
            ('2029-30', '2029-30'),
        ]
        self.fields['session'] = forms.ChoiceField(
            choices=SESSION_CHOICES,
            widget=forms.Select(attrs={'class': SELECT_CLASS}),
            required=True,
            label="Session"
        )
        
        # Apply INPUT_CLASS to all plain address fields
        addr_fields = [
            'present_village','present_post','present_post_code',
            'present_upazila','present_district','present_division',
            'permanent_village','permanent_post','permanent_post_code',
            'permanent_upazila','permanent_district','permanent_division',
        ]
        for f in addr_fields:
            self.fields[f].widget = forms.TextInput(attrs={'class': INPUT_CLASS})

    def clean(self):
        cleaned_data = super().clean()
        password        = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        cd = self.cleaned_data
        instance.present_address = {
            'village':     cd.get('present_village', ''),
            'post_office': cd.get('present_post', ''),
            'post_code':   cd.get('present_post_code', ''),
            'upazila':     cd.get('present_upazila', ''),
            'district':    cd.get('present_district', ''),
            'division':    cd.get('present_division', ''),
        }
        instance.permanent_address = {
            'village':     cd.get('permanent_village', ''),
            'post_office': cd.get('permanent_post', ''),
            'post_code':   cd.get('permanent_post_code', ''),
            'upazila':     cd.get('permanent_upazila', ''),
            'district':    cd.get('permanent_district', ''),
            'division':    cd.get('permanent_division', ''),
        }
        if commit:
            instance.save()
        return instance


# Fee Management Forms
class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['amount', 'frequency', 'description', 'is_active']
        widgets = {
            'amount':       forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'frequency':    forms.Select(attrs={'class': SELECT_CLASS}),
            'description':  forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g., Monthly Rover Fund'}),
            'is_active':    forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }


class RoverFeeForm(forms.ModelForm):
    class Meta:
        model = RoverFee
        fields = ['amount', 'frequency', 'status', 'due_date', 'paid_date']
        widgets = {
            'amount':    forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'frequency': forms.Select(attrs={'class': SELECT_CLASS}),
            'status':    forms.Select(attrs={'class': SELECT_CLASS}),
            'due_date':  forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'is_active']
        widgets = {
            'title':   forms.TextInput(attrs={'class': INPUT_CLASS}),
            'content': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }


class FundTransactionForm(forms.ModelForm):
    class Meta:
        model = FundTransaction
        fields = ['amount', 'transaction_type', 'description', 'date', 'rover']
        widgets = {
            'amount':           forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'transaction_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'description':      forms.TextInput(attrs={'class': INPUT_CLASS}),
            'date':             forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'rover':            forms.Select(attrs={'class': SELECT_CLASS}),
        }


class AdminRoverFeeForm(forms.ModelForm):
    class Meta:
        model = RoverFee
        fields = ['rover', 'amount', 'frequency', 'due_date']
        widgets = {
            'rover': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'যেমন: 10.00'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# ==================== CUSTOM ADMIN ROVER PROFILE FORM ====================
class AdminRoverProfileForm(forms.ModelForm):
    # শুধুমাত্র অলরেডি অ্যাপ্রুভড রভার প্রোফাইল সিলেক্ট করার ড্রপডাউন ফিল্ড
    rover_profile_select = forms.ModelChoiceField(
        queryset=RoverProfile.objects.filter(is_approved=True),
        required=True,
        empty_label="--- Select Approved Rover Profile ---",
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )

    class Meta:
        model = RoverProfile
        # এই কুইক ফর্মে আমরা শুধু rank এবং stage ফিল্ড ইনপুট নিচ্ছি
        fields = ['rank', 'stage']
        
        widgets = {
            # নতুন যুক্ত হওয়া র‍্যাংক এবং স্টেজ ড্রপডাউন (আপনার SELECT_CLASS থিমে)
            'rank':  forms.Select(attrs={'class': SELECT_CLASS}),
            'stage': forms.Select(attrs={'class': SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # শুধুমাত্র অ্যাপ্রুভড রভার প্রোফাইল রোল নম্বর অনুযায়ী সর্ট হয়ে ড্রপডাউনে দেখাবে
        self.fields['rover_profile_select'].queryset = RoverProfile.objects.filter(is_approved=True).order_by('roll_no')
        
        # ড্রপডাউনের ভেতরে রোল এবং নাম একসাথে সুন্দর করে দেখানোর জন্য কাস্টম লেবেল
        self.fields['rover_profile_select'].label_from_instance = lambda obj: f"Roll: {obj.roll_no} — {obj.name_en or 'No Name'}"
        
        # র‍্যাংক ও স্টেজের প্রথম অপশনটি সুন্দর দেখানোর জন্য ফাঁকা বা ডিফল্ট টেক্সট সেট করা
        self.fields['rank'].empty_label = "-- Select Rank --"
        self.fields['stage'].empty_label = "-- Select Stage --"