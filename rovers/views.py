from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from .forms import RoverRegistrationForm, FeeStructureForm, AdminRoverFeeForm, NoticeForm
import csv

from .models import RoverProfile, Notice, FeeStructure, RoverFee, FundTransaction
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RoverRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract fields
            roll_no = form.cleaned_data.get('roll_no')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            if User.objects.filter(username=roll_no).exists():
                form.add_error('roll_no', 'A user with this Roll Number already exists.')
                return render(request, 'rovers/register.html', {'form': form})
            else:
                # Create auth user
                user = User.objects.create_user(username=roll_no, email=email, password=password)
                # Save linked RoverProfile
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                # Log in and redirect
                login(request, user)
                return redirect('dashboard')
        # If form invalid or duplicate, re-render with errors
    else:
        form = RoverRegistrationForm()

    return render(request, 'rovers/register.html', {'form': form})

def home_view(request):
    notices = Notice.objects.filter(is_active=True)[:3]
    stats = {
        'total_rovers': RoverProfile.objects.filter(is_approved=True).count()
    }
    return render(request, 'home.html', {'notices': notices, 'stats': stats})

@login_required
def dashboard_view(request):
    try:
        profile = request.user.rover_profile
    except RoverProfile.DoesNotExist:
        profile = None

    context = {'profile': profile}

    # If the user is staff/admin, add aggregated stats for the admin dashboard
    if request.user.is_staff:
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
        # For regular rovers, add notices and fees
        context['notices'] = Notice.objects.filter(is_active=True).order_by('-created_at')
        if profile:
            context['pending_fees'] = profile.fees.filter(status='PENDING').order_by('due_date')
            context['fee_structure'] = FeeStructure.objects.filter(is_active=True).first()

    return render(request, 'rovers/dashboard.html', context)

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
        user.delete()
    return redirect('dashboard')

@user_passes_test(lambda u: u.is_staff)
def blood_directory_view(request):
    profiles = RoverProfile.objects.filter(is_approved=True)
    
    # Filtering
    blood_group = request.GET.get('blood_group')
    department = request.GET.get('department')
    session = request.GET.get('session')
    
    if blood_group:
        profiles = profiles.filter(blood_group=blood_group)
    if department:
        profiles = profiles.filter(department=department)
    if session:
        profiles = profiles.filter(session__icontains=session)
        
    # Export to CSV
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="blood_directory.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Form Number', 'Name', 'Blood Group', 'Department', 'Session', 'Mobile', 'Email'])
        
        for profile in profiles:
            writer.writerow([
                profile.form_number,
                profile.name_en,
                profile.blood_group,
                profile.department,
                profile.session,
                profile.mobile,
                profile.email
            ])
            
        return response

    context = {
        'profiles': profiles,
        'blood_group_param': blood_group,
        'department_param': department,
        'session_param': session,
    }
    return render(request, 'rovers/blood_directory.html', context)

# New views for Notice & Events and Fund Transactions (admin only)

@login_required
def notice_list(request):
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'rovers/notice_list.html', {'notices': notices})

@user_passes_test(lambda u: u.is_staff)
def fundtransaction_list(request):
    # ইউআরএল থেকে ফিল্টার স্ট্যাটাস নেওয়া (All, PENDING, PAID)
    status_filter = request.GET.get('status', '')

    # টেমপ্লেটের চাহিদা অনুযায়ী RoverFee মডেল থেকে ডেটা কুয়েরি করা
    if status_filter:
        rover_fees = RoverFee.objects.filter(status=status_filter).order_by('-due_date')
    else:
        rover_fees = RoverFee.objects.all().order_by('-due_date')

    # টেমপ্লেটে ঠিক যে ভ্যারিয়েবল নামগুলো দরকার, সেগুলো কনটেক্সটে পাঠানো হচ্ছে
    context = {
        'rover_fees': rover_fees,
        'status_filter': status_filter,
    }
    
    return render(request, 'rovers/admin_rover_fees_list.html', context)

# Fee Management Views

@user_passes_test(lambda u: u.is_staff)
def fee_structure_edit(request):
    """Admin view to configure fee structure (amount and frequency)"""
    fee_structure = FeeStructure.objects.first()
    
    if request.method == 'POST':
        if fee_structure:
            form = FeeStructureForm(request.POST, instance=fee_structure)
        else:
            form = FeeStructureForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        if fee_structure:
            form = FeeStructureForm(instance=fee_structure)
        else:
            form = FeeStructureForm()
    
    return render(request, 'rovers/admin_fee_structure.html', {'form': form, 'fee_structure': fee_structure})

@user_passes_test(lambda u: u.is_staff)
def rover_fees_list(request):
    """Admin view to see all rover fees and manage them"""
    rover_fees = RoverFee.objects.all().order_by('-due_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        rover_fees = rover_fees.filter(status=status_filter)
    
    context = {
        'rover_fees': rover_fees,
        'status_filter': status_filter,
    }
    return render(request, 'rovers/admin_rover_fees_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def rover_fee_mark_paid(request, fee_id):
    """Mark a fee as paid and auto-generate next fee"""
    fee = get_object_or_404(RoverFee, pk=fee_id)
    
    if request.method == 'POST':
        fee.status = 'PAID'
        fee.paid_date = datetime.now().date()
        fee.save()
        
        # Auto-create next fee
        try:
            fee_structure = FeeStructure.objects.filter(is_active=True).first()
            if fee_structure:
                # Calculate next due date
                if fee_structure.frequency == 'WEEKLY':
                    next_due_date = fee.due_date + timedelta(days=7)
                else:  # MONTHLY
                    next_due_date = fee.due_date + timedelta(days=30)
                
                RoverFee.objects.create(
                    rover=fee.rover,
                    amount=fee_structure.amount,
                    frequency=fee_structure.frequency,
                    status='PENDING',
                    due_date=next_due_date
                )
        except FeeStructure.DoesNotExist:
            pass
    
    return redirect('rover_fees_list')

@login_required
def my_fees(request):
    """Rover view to see their own fees"""
    try:
        profile = request.user.rover_profile
        fees = profile.fees.all()
        fee_structure = FeeStructure.objects.filter(is_active=True).first()
    except RoverProfile.DoesNotExist:
        profile = None
        fees = []
        fee_structure = None
    
    context = {
        'profile': profile,
        'fees': fees,
        'fee_structure': fee_structure,
    }
    return render(request, 'rovers/my_fees.html', context)
# rovers/views.py এর নিচে যোগ করুন
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AdminRoverFeeForm
from .models import FeeStructure

def add_rover_fee_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AdminRoverFeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.status = 'PENDING'
            fee.save()
            messages.success(request, "রোভারের পেন্ডিং ফি সফলভাবে যোগ করা হয়েছে!")
            
            # 'funds_list' পরিবর্তন করে আপনার আসল ইউআরএল নাম 'fundtransaction_list' দেওয়া হলো:
            return redirect('fundtransaction_list')
    else:
        # ডিফল্ট অ্যাক্টিভ ফি স্ট্রাকচার থাকলে সেটা ফর্মে আগে থেকেই বসিয়ে দেবে
        active_structure = FeeStructure.objects.filter(is_active=True).first()
        initial_data = {}
        if active_structure:
            initial_data = {
                'amount': active_structure.amount,
                'frequency': active_structure.frequency
            }
        form = AdminRoverFeeForm(initial=initial_data)
        
    return render(request, 'rovers/admin_add_fee.html', {'form': form})


# ===== NEW VIEWS FOR ADMIN =====

@user_passes_test(lambda u: u.is_staff)
def rover_list_all(request):
    """Admin view to see all rovers (approved + pending)"""
    # Get filters from request
    status_filter = request.GET.get('status', 'all')  # all, approved, pending
    department_filter = request.GET.get('department', '')
    session_filter = request.GET.get('session', '')
    
    # Start with all rovers
    rovers = RoverProfile.objects.all().order_by('-created_at')
    
    # Apply status filter
    if status_filter == 'approved':
        rovers = rovers.filter(is_approved=True)
    elif status_filter == 'pending':
        rovers = rovers.filter(is_approved=False)
    
    # Apply department filter
    if department_filter:
        rovers = rovers.filter(department=department_filter)
    
    # Apply session filter
    if session_filter:
        rovers = rovers.filter(session__icontains=session_filter)
    
    # Get counts for stats
    total_count = RoverProfile.objects.count()
    approved_count = RoverProfile.objects.filter(is_approved=True).count()
    pending_count = RoverProfile.objects.filter(is_approved=False).count()
    
    context = {
        'rovers': rovers,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'session_filter': session_filter,
        'total_count': total_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
    }
    return render(request, 'rovers/admin_rover_list_all.html', context)


@user_passes_test(lambda u: u.is_staff)
def notice_create(request):
    """Admin view to create and post notices"""
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notice_list')
    else:
        form = NoticeForm()
    
    # Get recent notices for preview
    recent_notices = Notice.objects.all().order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'recent_notices': recent_notices,
    }
    return render(request, 'rovers/admin_notice_create.html', context)


@user_passes_test(lambda u: u.is_staff)
def notice_edit(request, pk):
    """Admin view to edit notices"""
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            return redirect('notice_list')
    else:
        form = NoticeForm(instance=notice)
    
    context = {'form': form, 'notice': notice}
    return render(request, 'rovers/admin_notice_create.html', context)


@user_passes_test(lambda u: u.is_staff)
def notice_delete(request, pk):
    """Admin view to delete notices"""
    notice = get_object_or_404(Notice, pk=pk)
    
    if request.method == 'POST':
        notice.delete()
        return redirect('notice_list')
    
    context = {'notice': notice}
    return render(request, 'rovers/admin_notice_delete.html', context)