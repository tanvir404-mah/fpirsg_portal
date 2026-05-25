import csv
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.views.decorators.http import require_http_methods

from .models import RoverProfile, Notice, FeeStructure, RoverFee, FundTransaction, LeaderBoard, RoverRank, RoverStage
from .forms import RoverRegistrationForm, FeeStructureForm, AdminRoverFeeForm, NoticeForm, AdminRoverProfileForm


# ==================== PUBLIC & AUTH VIEWS ====================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RoverRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            roll_no = form.cleaned_data.get('roll_no')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            if User.objects.filter(username=roll_no).exists():
                form.add_error('roll_no', 'A user with this Roll Number already exists.')
                return render(request, 'rovers/register.html', {'form': form})
            else:
                user = User.objects.create_user(username=roll_no, email=email, password=password)
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                login(request, user)
                return redirect('dashboard')
    else:
        form = RoverRegistrationForm()

    return render(request, 'rovers/register.html', {'form': form})


def home_view(request):
    notices = Notice.objects.filter(is_active=True)[:3]
    leaders = LeaderBoard.objects.all().order_by('order')
    stats = {
        'total_rovers': RoverProfile.objects.filter(is_approved=True).count()
    }
    return render(request, 'home.html', {
        'notices': notices, 
        'stats': stats,
        'leaders': leaders
    })


# ==================== MAIN DASHBOARD ====================

@login_required
def dashboard_view(request):
    try:
        # এখানে আপনার আগের কোডের স্পেলিংটা (rover_profile) ঠিক করা হয়েছে যেন ক্রাশ না করে
        profile = request.user.rover_profile  
    except RoverProfile.DoesNotExist:
        profile = None

    context = {'profile': profile}

    # If the user is staff/admin, add aggregated stats for the admin dashboard
    if request.user.is_staff:
        
        # -----------------------------------------------------------------
        # 🛠️ আপনার পুরনো কোড বদলে শুধু কাজের কুইক আপডেট লজিক রাখা হলো
        # -----------------------------------------------------------------
        if request.method == 'POST' and 'add_rover_submit' in request.POST:
            form = AdminRoverProfileForm(request.POST)
            if form.is_valid():
                # ১. ড্রপডাউন থেকে সিলেক্ট করা রভার প্রোফাইল অবজেক্টটি ধরা
                selected_profile = form.cleaned_data.get('rover_profile_select')
                
                if selected_profile:
                    # ২. ফর্ম থেকে আসা নতুন র‍্যাংক এবং স্টেজ অ্যাসাইন করা
                    selected_profile.rank = form.cleaned_data.get('rank')
                    selected_profile.stage = form.cleaned_data.get('stage')
                    
                    # ৩. ডাটাবেজে আপডেট ডাটা সেভ করা (কোনো নতুন ইউজার বা রোল ক্রিয়েশন হবে না)
                    selected_profile.save()
                    
                    messages.success(request, f"Rover {selected_profile.name_en} (Roll: {selected_profile.roll_no})- Rank ও Stage Sucessfully Updated!")
                else:
                    messages.error(request, "No Rover selected for updating Rank & Stage.")
                    
                return redirect('dashboard')
        else:
            form = AdminRoverProfileForm()

        context['form'] = form
        # -----------------------------------------------------------------
        
        # আপনার আগের হুবহু সব কোড (১ অক্ষরেরও পরিবর্তন নেই)
        context['total_rovers'] = RoverProfile.objects.filter(is_approved=True).count()
        context['pending_requests'] = RoverProfile.objects.filter(is_approved=False).count()
        context['active_donors'] = RoverProfile.objects.filter(is_approved=True).exclude(blood_group='').count()
        
        # Calculate current month's funds (simplified to all-time income for now, can be filtered by month)
        total_funds = FundTransaction.objects.filter(transaction_type='IN').aggregate(total=Sum('amount'))['total'] or 0
        context['total_funds'] = total_funds
        
        # Data for quick actions table
        context['pending_rovers_list'] = RoverProfile.objects.filter(is_approved=False).order_by('-created_at')[:10]
        
        # Data for Chart.js
        # Blood Group Distribution
        bg_distribution = list(RoverProfile.objects.filter(is_approved=True).values('blood_group').annotate(count=Count('id')))
        context['bg_distribution'] = bg_distribution
        
        # Department Distribution
        dept_distribution = list(RoverProfile.objects.filter(is_approved=True).values('department').annotate(count=Count('id')))
        context['dept_distribution'] = dept_distribution
    else:
        # For regular rovers, add notices and fees (আপনার আগের কোড)
        context['notices'] = Notice.objects.filter(is_active=True).order_by('-created_at')
        if profile:
            context['pending_fees'] = profile.fees.filter(status='PENDING').order_by('due_date')
            context['fee_structure'] = FeeStructure.objects.filter(is_active=True).first()

    return render(request, 'rovers/dashboard.html', context)


# ==================== CUSTOM ADMIN: ROVER MANAGEMENT (র‍্যাংক ও স্টেজ সহ) ====================

@user_passes_test(lambda u: u.is_staff)
def add_rover_member(request):
    """কাস্টম ড্যাশবোর্ড থেকে অলরেডি অ্যাপ্রুভড রভার সিলেক্ট করে দ্রুত র‍্যাংক ও স্টেজ আপডেট করার ভিউ"""
    if request.method == 'POST':
        form = AdminRoverProfileForm(request.POST)
        if form.is_valid():
            # ১. ফর্মের ড্রপডাউন থেকে সিলেক্ট করা এক্সিস্টিং রভার প্রোফাইল অবজেক্টটি ধরা
            selected_profile = form.cleaned_data.get('rover_profile_select')
            
            # ২. ফর্ম থেকে নতুন সিলেক্ট করা র‍্যাংক এবং স্টেজ অ্যাসাইন করা
            selected_profile.rank = form.cleaned_data.get('rank')
            selected_profile.stage = form.cleaned_data.get('stage')
            
            # ৩. আপডেট হওয়া ডাটা ডাটাবেজে সেভ করা
            selected_profile.save()
            
            messages.success(
                request, 
                f"রভার {selected_profile.name_en} (রোল: {selected_profile.roll_no})-এর Rank ও Stage সফলভাবে আপডেট করা হয়েছে!"
            )
            # আপডেট শেষে আপনার আগের রিডাইরেক্টিং ইউআরএল (অথবা আপনার ড্যাশবোর্ডেও পাঠাতে পারেন)
            return redirect('rover_list_all')
    else:
        form = AdminRoverProfileForm()
        
    return render(request, 'rovers/dashboard', {'form': form, 'title': 'Update Rover Rank & Stage'})


@user_passes_test(lambda u: u.is_staff)
def approve_rover(request, pk):
    rover = get_object_or_404(RoverProfile, pk=pk)
    if request.method == 'POST':
        rover.is_approved = True
        rover.save()
    return redirect('dashboard')


@user_passes_test(lambda u: u.is_staff)
def reject_rover(request, pk):
    rover = get_object_or_404(RoverProfile, pk=pk)
    if request.method == 'POST':
        user = rover.user
        rover.delete()
        if user:
            user.delete()
    return redirect('dashboard')


@user_passes_test(lambda u: u.is_staff)
def rover_list_all(request):
    status_filter = request.GET.get('status', 'all')
    department_filter = request.GET.get('department', '')
    session_filter = request.GET.get('session', '')
    
    rovers = RoverProfile.objects.all().order_by('-created_at')
    
    if status_filter == 'approved':
        rovers = rovers.filter(is_approved=True)
    elif status_filter == 'pending':
        rovers = rovers.filter(is_approved=False)
    
    if department_filter:
        rovers = rovers.filter(department=department_filter)
    
    if session_filter:
        rovers = rovers.filter(session__icontains=session_filter)
    
    context = {
        'rovers': rovers,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'session_filter': session_filter,
        'total_count': RoverProfile.objects.count(),
        'approved_count': RoverProfile.objects.filter(is_approved=True).count(),
        'pending_count': RoverProfile.objects.filter(is_approved=False).count(),
    }
    return render(request, 'rovers/admin_rover_list_all.html', context)


# ==================== GENERAL PROFILE VIEWS ====================

@login_required
def rover_profile_view(request):
    try:
        profile = request.user.rover_profile  # ফিক্সড স্পেলিং ক্র্যাশ বাগ
    except RoverProfile.DoesNotExist:
        profile = None
        
    return render(request, 'rovers/profile.html', {'profile': profile})


@user_passes_test(lambda u: u.is_staff)
def rover_profile_detail_view(request, pk):
    rover = get_object_or_404(RoverProfile, pk=pk)
    fees = rover.fees.all().order_by('-due_date')
    return render(request, 'rovers/admin_rover_profile_detail.html', {'rover': rover, 'fees': fees})


# ==================== BLOOD DONATION DIRECTORY ====================

@user_passes_test(lambda u: u.is_staff)
def blood_directory_view(request):
    profiles = RoverProfile.objects.filter(is_approved=True)
    
    blood_group = request.GET.get('blood_group')
    department = request.GET.get('department')
    session = request.GET.get('session')
    
    if blood_group:
        profiles = profiles.filter(blood_group=blood_group)
    if department:
        profiles = profiles.filter(department=department)
    if session:
        profiles = profiles.filter(session__icontains=session)
        
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="blood_directory.csv"'
        writer = csv.writer(response)
        writer.writerow(['Form Number', 'Name', 'Blood Group', 'Department', 'Session', 'Mobile', 'Email'])
        for profile in profiles:
            writer.writerow([profile.form_number, profile.name_en, profile.blood_group, profile.department, profile.session, profile.mobile, profile.email])
        return response

    context = {
        'profiles': profiles,
        'blood_group_param': blood_group,
        'department_param': department,
        'session_param': session,
    }
    return render(request, 'rovers/blood_directory.html', context)


# ==================== FEE & FUND MANAGEMENT ====================

@user_passes_test(lambda u: u.is_staff)
def fundtransaction_list(request):
    status_filter = request.GET.get('status', '')
    if status_filter:
        rover_fees = RoverFee.objects.filter(status=status_filter).order_by('-due_date')
    else:
        rover_fees = RoverFee.objects.all().order_by('-due_date')

    return render(request, 'rovers/admin_rover_fees_list.html', {'rover_fees': rover_fees, 'status_filter': status_filter})


@user_passes_test(lambda u: u.is_staff)
def fee_structure_edit(request):
    fee_structure = FeeStructure.objects.first()
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure) if fee_structure else FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = FeeStructureForm(instance=fee_structure) if fee_structure else FeeStructureForm()
    
    return render(request, 'rovers/admin_fee_structure.html', {'form': form, 'fee_structure': fee_structure})


@user_passes_test(lambda u: u.is_staff)
def rover_fees_list(request):
    rover_fees = RoverFee.objects.all().order_by('-due_date')
    status_filter = request.GET.get('status')
    if status_filter:
        rover_fees = rover_fees.filter(status=status_filter)
    
    return render(request, 'rovers/admin_rover_fees_list.html', {'rover_fees': rover_fees, 'status_filter': status_filter})


@user_passes_test(lambda u: u.is_staff)
def rover_fee_mark_paid(request, fee_id):
    fee = get_object_or_404(RoverFee, pk=fee_id)
    if request.method == 'POST':
        fee.status = 'PAID'
        fee.paid_date = datetime.now().date()
        fee.save()
        
        try:
            fee_structure = FeeStructure.objects.filter(is_active=True).first()
            if fee_structure:
                next_due_date = fee.due_date + timedelta(days=7) if fee_structure.frequency == 'WEEKLY' else fee.due_date + timedelta(days=30)
                RoverFee.objects.create(rover=fee.rover, amount=fee_structure.amount, frequency=fee_structure.frequency, status='PENDING', due_date=next_due_date)
        except FeeStructure.DoesNotExist:
            pass
    return redirect('rover_fees_list')


@login_required
def my_fees(request):
    try:
        profile = request.user.rover_profile
        fees = profile.fees.all()
        fee_structure = FeeStructure.objects.filter(is_active=True).first()
    except RoverProfile.DoesNotExist:
        profile, fees, fee_structure = None, [], None
    
    return render(request, 'rovers/my_fees.html', {'profile': profile, 'fees': fees, 'fee_structure': fee_structure})


@user_passes_test(lambda u: u.is_staff)
def add_rover_fee_view(request):
    if request.method == 'POST':
        form = AdminRoverFeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.status = 'PENDING'
            fee.save()
            messages.success(request, "রোভারের পেন্ডিং ফি সফলভাবে যোগ করা হয়েছে!")
            return redirect('fundtransaction_list')
    else:
        active_structure = FeeStructure.objects.filter(is_active=True).first()
        initial_data = {'amount': active_structure.amount, 'frequency': active_structure.frequency} if active_structure else {}
        form = AdminRoverFeeForm(initial=initial_data)
        
    return render(request, 'rovers/admin_add_fee.html', {'form': form})


# ==================== NOTICE MANAGEMENT ====================

@login_required
def notice_list(request):
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'rovers/notice_list.html', {'notices': notices})


@user_passes_test(lambda u: u.is_staff)
def notice_create(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notice_list')
    else:
        form = NoticeForm()
    
    return render(request, 'rovers/admin_notice_create.html', {'form': form, 'recent_notices': Notice.objects.all().order_by('-created_at')[:5]})


@user_passes_test(lambda u: u.is_staff)
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            return redirect('notice_list')
    else:
        form = NoticeForm(instance=notice)
    return render(request, 'rovers/admin_notice_create.html', {'form': form, 'notice': notice})


@user_passes_test(lambda u: u.is_staff)
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        return redirect('notice_list')
    return render(request, 'rovers/admin_notice_delete.html', {'notice': notice})


# ==================== ADVANCED VERIFICATION DASHBOARD ====================

def calculate_profile_completeness(rover):
    fields = [
        ('name_en', 'Name (English)'), ('name_bn', 'Name (Bangla)'),
        ('father_name_en', "Father's Name (English)"), ('father_name_bn', "Father's Name (Bangla)"),
        ('mother_name_en', "Mother's Name (English)"), ('mother_name_bn', "Mother's Name (Bangla)"),
        ('dob', 'Date of Birth'), ('religion', 'Religion'), ('blood_group', 'Blood Group'),
        ('mobile', 'Mobile Number'), ('guardian_mobile', 'Guardian Mobile'), ('email', 'Email'),
        ('present_address', 'Present Address'), ('permanent_address', 'Permanent Address'),
        ('ssc_year', 'SSC Year'), ('ssc_gpa', 'SSC GPA'), ('department', 'Department'),
        ('session', 'Session'), ('semester', 'Semester'), ('shift', 'Shift'), ('roll_no', 'Roll No'),
        ('profile_pic', 'Profile Picture'),
    ]
    missing_fields = []
    completed_fields = 0
    for field_name, field_label in fields:
        if not getattr(rover, field_name, None):
            missing_fields.append(field_label)
        else:
            completed_fields += 1
    return {
        'percentage': int((completed_fields / len(fields)) * 100),
        'completed': completed_fields,
        'total': len(fields),
        'missing': missing_fields
    }


@user_passes_test(lambda u: u.is_staff)
def rover_verification_dashboard(request):
    status_filter = request.GET.get('status', 'all')
    completeness_filter = request.GET.get('completeness', 'all')
    department_filter = request.GET.get('department', '')
    session_filter = request.GET.get('session', '')
    search_query = request.GET.get('search', '')
    
    rovers = RoverProfile.objects.all().order_by('-created_at')
    
    if status_filter == 'approved':
        rovers = rovers.filter(is_approved=True)
    elif status_filter == 'pending':
        rovers = rovers.filter(is_approved=False)
    
    if department_filter:
        rovers = rovers.filter(department=department_filter)
    if session_filter:
        rovers = rovers.filter(session__icontains=session_filter)
    if search_query:
        rovers = rovers.filter(
            Q(name_en__icontains=search_query) | Q(name_bn__icontains=search_query) |
            Q(roll_no__icontains=search_query) | Q(form_number__icontains=search_query) |
            Q(email__icontains=search_query) | Q(mobile__icontains=search_query)
        )
    
    rovers_data = []
    for rover in rovers:
        completeness = calculate_profile_completeness(rover)
        if completeness_filter == 'complete' and completeness['percentage'] < 100:
            continue
        elif completeness_filter == 'incomplete' and completeness['percentage'] == 100:
            continue
        rovers_data.append({'rover': rover, 'completeness': completeness})
    
    context = {
        'rovers_data': rovers_data,
        'status_filter': status_filter,
        'completeness_filter': completeness_filter,
        'department_filter': department_filter,
        'session_filter': session_filter,
        'search_query': search_query,
        'total_count': RoverProfile.objects.count(),
        'approved_count': RoverProfile.objects.filter(is_approved=True).count(),
        'pending_count': RoverProfile.objects.filter(is_approved=False).count(),
        'complete_profiles': sum(1 for r in rovers_data if r['completeness']['percentage'] == 100),
        'incomplete_profiles': len(rovers_data) - sum(1 for r in rovers_data if r['completeness']['percentage'] == 100),
        'departments': RoverProfile.objects.values_list('department', flat=True).distinct(),
        'sessions': RoverProfile.objects.values_list('session', flat=True).distinct(),
    }
    return render(request, 'rovers/admin_verification_dashboard.html', context)