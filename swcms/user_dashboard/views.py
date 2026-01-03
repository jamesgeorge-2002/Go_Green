from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from collections import defaultdict
from .forms import UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm, LoginForm, PickupRequestForm, FeedbackForm, WasteWeightForm, UserProfileEditForm, ProfileEditForm
from .models import PickupRequest, Reward, Profile, Ward, Payment, Feedback, Panchayath
import io
from django.http import HttpResponse

# Decorator for role-based access
def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                profile = Profile.objects.get(user=request.user)
                if profile.role not in allowed_roles:
                    messages.error(request, "Access denied. You don't have permission to access this page.")
                    return redirect('index')
            except Profile.DoesNotExist:
                messages.error(request, "Profile not found. Please contact administrator.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@login_required
def index(request):
    try:
        user = request.user
        profile = Profile.objects.get(user=user)
        
        # Only users should access this page
        if profile.role != 'user':
            if profile.role == 'admin':
                return redirect('admin_dashboard')
            elif profile.role == 'worker':
                return redirect('worker_dashboard')
        
        reward, created = Reward.objects.get_or_create(user=user)
        reward_points = reward.points
        upcoming_pickups = PickupRequest.objects.filter(user=user, schedule_date_time__gte=timezone.now(), status__in=['pending', 'picked']).order_by('schedule_date_time')
        previous_pickups = PickupRequest.objects.filter(user=user, schedule_date_time__lt=timezone.now()).order_by('-schedule_date_time')[:5]
        total_pickups = PickupRequest.objects.filter(user=user, status='completed').count()

        context = {
            'reward_points': reward_points,
            'upcoming_pickups': upcoming_pickups,
            'previous_pickups': previous_pickups,
            'total_pickups': total_pickups,
        }
        return render(request, 'user_dashboard/index.html', context)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Please contact administrator.")
        return redirect('login')

def user_register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='user')
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def worker_register_view(request):
    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile and ward are created inside the form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def admin_register_view(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile and ward are created inside the form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = AdminRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on role
                try:
                    profile = Profile.objects.get(user=user)
                    if profile.role == 'admin':
                        return redirect('admin_dashboard')
                    elif profile.role == 'worker':
                        return redirect('worker_dashboard')
                    else:
                        return redirect('index')
                except Profile.DoesNotExist:
                    return redirect('index')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, 'user_dashboard/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def edit_profile_view(request):
    """Allow users to edit their profile information"""
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found.")
        return redirect('index')

    if request.method == 'POST':
        user_form = UserProfileEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('index')
    else:
        user_form = UserProfileEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'user_dashboard/edit_profile.html', context)

@login_required
def request_pickup_view(request):
    if request.method == 'POST':
        form = PickupRequestForm(request.POST, request.FILES)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.user = request.user
            pickup.save()
            messages.success(request, 'Pickup request submitted successfully.')
            return redirect('payment', pk=pickup.pk)
    else:
        form = PickupRequestForm()
    return render(request, 'user_dashboard/request_pickup.html', {'form': form})

@login_required
def pickup_detail_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    try:
        payment = pickup.payment
    except Payment.DoesNotExist:
        payment = None
    return render(request, 'user_dashboard/pickup_detail.html', {'pickup': pickup, 'payment': payment})

@login_required
def payment_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    
    # Get or create payment record
    payment, created = Payment.objects.get_or_create(
        pickup_request=pickup,
        user=request.user,
        defaults={'amount': Decimal('100.00')}  # Default amount, adjust as needed
    )
    
    # Context data for Razorpay
    context = {
        'pickup': pickup,
        'payment': payment,
        'amount': int(payment.amount * 100),  # Razorpay expects amount in paise
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': payment.razorpay_order_id or '',
        'user': request.user,
    }
    return render(request, 'user_dashboard/payment.html', context)

@login_required
def request_management_view(request):
    pickups = PickupRequest.objects.filter(user=request.user).order_by('-created_at')

    # Fetch payments for these pickups and map by pickup pk
    payments = Payment.objects.filter(user=request.user, pickup_request__in=pickups)
    payment_map = {p.pickup_request_id: p for p in payments}

    # Build rows with pickup and optional payment to avoid template related-object errors
    rows = []
    for p in pickups:
        rows.append({'pickup': p, 'payment': payment_map.get(p.pk)})

    return render(request, 'user_dashboard/request_management.html', {'rows': rows})

@login_required
def cancel_request_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    if pickup.status == 'pending':
        pickup.status = 'cancelled'
        pickup.save()
        messages.success(request, 'Request cancelled.')
    elif pickup.status == 'completed':
        messages.error(request, 'Cannot cancel completed requests.')
    elif pickup.status == 'picked':
        messages.error(request, 'Cannot cancel requests that are already picked up.')
    else:
        messages.error(request, 'Cannot cancel this request in its current status.')
    return redirect('request_management')

@login_required
def payment_management_view(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_dashboard/payment_management.html', {'payments': payments})

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted.')
            return redirect('index')
    else:
        form = FeedbackForm()
    return render(request, 'user_dashboard/feedback.html', {'form': form})

@login_required
def feedback_management_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role not in ['admin', 'worker']:
        messages.error(request, "Access denied.")
        return redirect('index')

    feedbacks = Feedback.objects.filter(ward=user_profile.ward).order_by('-created_at') if user_profile.role == 'worker' else Feedback.objects.all().order_by('-created_at')
    return render(request, 'user_dashboard/feedback_management.html', {'feedbacks': feedbacks})

@login_required
def resolve_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role not in ['admin', 'worker']:
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk, ward=user_profile.ward) if user_profile.role == 'worker' else get_object_or_404(Feedback, pk=pk)
    if feedback.status == 'pending':
        feedback.status = 'resolved'
        feedback.save()
        messages.success(request, "Feedback resolved.")
    else:
        messages.error(request, "Cannot resolve this feedback.")
    return redirect('feedback_management')

@login_required
def worker_dashboard_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied. Only workers can view this page.")
        return redirect('index')

    # Filter pickups by worker's ward
    pickups = PickupRequest.objects.filter(user__profile__ward=user_profile.ward).order_by('-created_at')

    pending_qs = pickups.filter(status='pending')
    picked_qs = pickups.filter(status='picked')
    completed_qs = pickups.filter(status='completed')

    # Attach payments to pickups to avoid RelatedObjectDoesNotExist in templates
    def attach_payments(qs):
        payments = Payment.objects.filter(pickup_request__in=qs)
        payment_map = {p.pickup_request_id: p for p in payments}
        return [{'pickup': p, 'payment': payment_map.get(p.pk)} for p in qs]

    pending_pickups = attach_payments(pending_qs)
    picked_pickups = attach_payments(picked_qs)
    completed_pickups = attach_payments(completed_qs)

    # Filter feedbacks by worker's ward
    feedbacks = Feedback.objects.filter(ward=user_profile.ward).order_by('-created_at')
    pending_feedbacks = feedbacks.filter(status='pending')
    resolved_feedbacks = feedbacks.filter(status='resolved')

    context = {
        'pending_pickups': pending_pickups,
        'picked_pickups': picked_pickups,
        'completed_pickups': completed_pickups,
        'pending_feedbacks': pending_feedbacks,
        'resolved_feedbacks': resolved_feedbacks,
    }
    return render(request, 'user_dashboard/worker_dashboard.html', context)


@login_required
@role_required(['worker'])
def collect_cash_view(request, pk):
    """Mark payment for a pickup as collected in cash."""
    user_profile = Profile.objects.get(user=request.user)
    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)

    try:
        payment = pickup.payment
    except Payment.DoesNotExist:
        # Create a payment record and mark as completed (cash)
        payment = Payment.objects.create(
            user=pickup.user,
            pickup_request=pickup,
            amount=Decimal('100.00'),
            status='completed',
            razorpay_payment_id='cash'
        )
        messages.success(request, 'Payment recorded as collected (cash).')
        return redirect('worker_dashboard')

    if payment.status == 'completed':
        messages.info(request, 'Payment was already completed.')
    else:
        payment.status = 'completed'
        payment.razorpay_payment_id = 'cash'
        payment.save()
        messages.success(request, 'Payment marked as collected (cash).')

    return redirect('worker_dashboard')

def _generate_pickup_receipt_pdf(pickup):
    """Generate a PDF receipt for a completed pickup."""
    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
    except ModuleNotFoundError:
        return None

    try:
        payment = pickup.payment
    except Payment.DoesNotExist:
        payment = None

    buffer = io.BytesIO()
    p = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 20 * mm
    x = margin
    y = height - margin

    p.setFont('Helvetica-Bold', 16)
    p.drawString(x, y, 'SWCMS - Waste Collection Receipt')
    y -= 12 * mm

    p.setFont('Helvetica', 10)
    p.drawString(x, y, f'Request ID: {pickup.request_id}')
    y -= 6 * mm
    p.drawString(x, y, f'Date: {pickup.updated_at.strftime("%Y-%m-%d %H:%M") if pickup.updated_at else pickup.created_at.strftime("%Y-%m-%d %H:%M")}')
    y -= 6 * mm

    p.setFont('Helvetica-Bold', 12)
    p.drawString(x, y, 'Customer Details')
    y -= 6 * mm
    p.setFont('Helvetica', 10)
    p.drawString(x, y, f'Name: {pickup.user.get_full_name() or pickup.user.username}')
    y -= 6 * mm
    p.drawString(x, y, f'Email: {pickup.user.email or "-"}')
    y -= 8 * mm

    p.setFont('Helvetica-Bold', 12)
    p.drawString(x, y, 'Pickup Details')
    y -= 6 * mm
    p.setFont('Helvetica', 10)
    p.drawString(x, y, f'Waste Type: {pickup.get_waste_type_display()}')
    y -= 6 * mm
    p.drawString(x, y, f'Weight (kg): {pickup.waste_weight}')
    y -= 6 * mm

    amount_text = 'N/A'
    payment_status = 'N/A'
    if payment:
        amount_text = f'₹{payment.amount}'
        payment_status = payment.get_status_display()

    y -= 4 * mm
    p.setFont('Helvetica-Bold', 12)
    p.drawString(x, y, 'Payment')
    y -= 6 * mm
    p.setFont('Helvetica', 10)
    p.drawString(x, y, f'Amount: {amount_text}')
    y -= 6 * mm
    p.drawString(x, y, f'Status: {payment_status}')
    y -= 12 * mm

    # Previous pickups summary
    previous_pickups = PickupRequest.objects.filter(
        user=pickup.user,
        status='completed'
    ).exclude(pk=pickup.pk).order_by('-created_at')[:5]

    if previous_pickups:
        p.setFont('Helvetica-Bold', 12)
        p.drawString(x, y, 'Previous Pickups (Last 5)')
        y -= 6 * mm
        p.setFont('Helvetica', 8)
        for prev in previous_pickups:
            prev_text = f"• {prev.get_waste_type_display()} - {prev.waste_weight}kg - {prev.created_at.strftime('%Y-%m-%d')}"
            p.drawString(x, y, prev_text)
            y -= 5 * mm
        y -= 2 * mm
    else:
        p.setFont('Helvetica', 8)
        p.drawString(x, y, '(No previous pickups)')
        y -= 5 * mm

    y -= 8 * mm
    p.setFont('Helvetica', 10)
    p.drawString(x, y, 'Thank you for using SWCMS. Please keep this receipt for your records.')
    y -= 20 * mm

    # Signature line
    p.line(x, y, x + 60 * mm, y)
    p.drawString(x, y - 5, 'Collector Signature')

    p.showPage()
    p.save()
    buffer.seek(0)

    return buffer

@login_required
def print_receipt_view(request, pk):
    """Print receipt for a completed pickup."""
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)

    if pickup.status != 'completed':
        messages.error(request, "Can only print receipts for completed pickups.")
        return redirect('worker_dashboard')

    buffer = _generate_pickup_receipt_pdf(pickup)
    if buffer is None:
        messages.warning(request, 'PDF generation requires the reportlab package.')
        return redirect('worker_dashboard')

    filename = f'receipt_{pickup.request_id}.pdf'
    resp = HttpResponse(buffer, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'

    return resp

@login_required
def mark_picked_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)
    if pickup.status == 'pending':
        pickup.status = 'picked'
        pickup.save()
        messages.success(request, "Pickup marked as picked.")
    else:
        messages.error(request, "Cannot mark this pickup as picked.")
    return redirect('worker_dashboard')

def _recalculate_user_rewards():
    """
    Recalculate reward points automatically based on total waste generated
    and its environmental impact. Users with less and less-harmful waste
    receive higher scores. Only users with role='user' are ranked.
    """
    # Weight multipliers per waste type (higher = more harmful)
    weight_factors = {
        'wet': Decimal('1.0'),
        'dry': Decimal('1.0'),
        'recyclable': Decimal('0.5'),
        'plastic': Decimal('2.0'),
        'e-waste': Decimal('3.0'),
    }

    impact_map = defaultdict(lambda: {'total_kg': Decimal('0'), 'impact': Decimal('0')})

    completed = (
        PickupRequest.objects
        .filter(status='completed')
        .select_related('user')
        .only('user_id', 'waste_type', 'waste_weight')
    )

    for p in completed:
        if p.waste_weight is None:
            continue
        if not hasattr(p, 'user') or p.user is None:
            continue
        weight = Decimal(str(p.waste_weight))
        factor = weight_factors.get(p.waste_type, Decimal('1.0'))
        impact_map[p.user]['total_kg'] += weight
        impact_map[p.user]['impact'] += weight * factor

    # Ensure all users with role 'user' exist in the map (even if zero waste)
    for profile in Profile.objects.select_related('user').filter(role='user'):
        _ = impact_map[profile.user]  # initialize default if missing

    users_impacts = list(impact_map.items())
    if not users_impacts:
        return

    # Sort by impact ascending (less impact = better)
    users_impacts.sort(key=lambda item: (item[1]['impact'], item[0].id))
    n = len(users_impacts)
    max_points = Decimal('100')
    min_points = Decimal('10')

    for idx, (user, data) in enumerate(users_impacts):
        # Linear scale: best user gets max_points, worst gets min_points
        if n == 1:
            points = max_points
        else:
            # rank 0 => best
            ratio = Decimal(n - 1 - idx) / Decimal(n - 1)  # 1.0 .. 0.0
            points = min_points + (max_points - min_points) * ratio
        reward, _ = Reward.objects.get_or_create(
            user=user,
            defaults={'points': 0, 'total_waste_collected': Decimal('0')},
        )
        reward.total_waste_collected = data['total_kg']
        reward.points = int(points)
        reward.save()

@login_required
@role_required(['worker'])
def mark_completed_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)

    if request.method == 'POST':
        form = WasteWeightForm(request.POST)
        if form.is_valid():
            waste_weight = form.cleaned_data['waste_weight']
            if pickup.status == 'picked':
                pickup.status = 'completed'
                pickup.waste_weight = waste_weight
                pickup.save()

                # Automatically recalculate rewards for all users
                _recalculate_user_rewards()

                # Generate PDF receipt
                buffer = _generate_pickup_receipt_pdf(pickup)
                if buffer is None:
                    messages.warning(request, 'PDF generation requires the reportlab package. Install it to enable receipts.')
                    return redirect('worker_dashboard')

                filename = f'receipt_{pickup.request_id}.pdf'
                resp = HttpResponse(buffer, content_type='application/pdf')
                resp['Content-Disposition'] = f'attachment; filename="{filename}"'

                return resp
            else:
                messages.error(request, "Cannot mark this pickup as completed.")
            return redirect('worker_dashboard')
    else:
        form = WasteWeightForm()

    return render(request, 'user_dashboard/enter_weight.html', {'pickup': pickup, 'form': form})

@login_required
def admin_dashboard_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    users = User.objects.filter(profile__isnull=False)
    pickups = PickupRequest.objects.all()
    feedbacks = Feedback.objects.all()
    payments = Payment.objects.all()

    total_users = users.count()
    total_pickups = pickups.count()
    pending_pickups = pickups.filter(status='pending').count()
    completed_pickups = pickups.filter(status='completed').count()
    total_feedbacks = feedbacks.count()
    pending_feedbacks = feedbacks.filter(status='pending').count()
    total_payments = payments.count()

    context = {
        'total_users': total_users,
        'total_pickups': total_pickups,
        'pending_pickups': pending_pickups,
        'completed_pickups': completed_pickups,
        'total_feedbacks': total_feedbacks,
        'pending_feedbacks': pending_feedbacks,
        'total_payments': total_payments,
    }
    return render(request, 'user_dashboard/admin_dashboard.html', context)

@login_required
@role_required(['admin'])
def admin_users_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    users = User.objects.filter(profile__isnull=False)
    wards = Ward.objects.all()

    context = {
        'users': users,
        'wards': wards,
    }
    return render(request, 'user_dashboard/admin_users.html', context)

@login_required
@role_required(['admin'])
def admin_feedbacks_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    feedbacks = Feedback.objects.all().order_by('-created_at')

    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'user_dashboard/admin_feedbacks.html', context)

@login_required
@role_required(['admin'])
def admin_wards_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    wards = Ward.objects.all()

    context = {
        'wards': wards,
    }
    return render(request, 'user_dashboard/admin_wards.html', context)

@login_required
@role_required(['admin'])
def admin_rewards_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    rewards = Reward.objects.filter(user__profile__role='user').order_by('-points')
    user_with_least_waste = rewards.order_by('total_waste_collected').first()

    context = {
        'rewards': rewards,
        'user_with_least_waste': user_with_least_waste,
    }
    return render(request, 'user_dashboard/admin_rewards.html', context)

@login_required
@role_required(['admin'])
def admin_mark_picked_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk)
    if pickup.status == 'pending':
        pickup.status = 'picked'
        pickup.save()
        messages.success(request, "Pickup marked as picked.")
    else:
        messages.error(request, "Cannot mark this pickup as picked.")
    return redirect('admin_users')

@login_required
@role_required(['admin'])
def admin_mark_completed_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk)
    if pickup.status == 'picked':
        pickup.status = 'completed'
        pickup.save()
        messages.success(request, "Pickup marked as completed.")
    else:
        messages.error(request, "Cannot mark this pickup as completed.")
    return redirect('admin_users')

@login_required
@role_required(['admin'])
def admin_resolve_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk)
    if feedback.status == 'pending':
        feedback.status = 'resolved'
        feedback.save()
        messages.success(request, "Feedback marked as resolved.")
    else:
        messages.error(request, "Cannot resolve this feedback.")
    return redirect('admin_feedbacks')

@login_required
@role_required(['admin'])
def admin_update_role_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['user', 'worker', 'admin']:
            profile = get_object_or_404(Profile, pk=pk)
            profile.role = new_role
            profile.save()
            messages.success(request, f"Role updated to {new_role}.")
        else:
            messages.error(request, "Invalid role.")
    return redirect('admin_users')

@login_required
@role_required(['admin'])
def admin_allocate_ward_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        ward_id = request.POST.get('ward')
        if ward_id:
            ward = get_object_or_404(Ward, pk=ward_id)
            profile = get_object_or_404(Profile, pk=pk)
            profile.ward = ward
            profile.save()
            messages.success(request, f"Ward allocated to {profile.user.username}.")
        else:
            messages.error(request, "Invalid ward.")
    return redirect('admin_users')

@login_required
@role_required(['admin'])
def admin_respond_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        response = request.POST.get('response')
        if response:
            feedback.response = response
            feedback.status = 'resolved'
            feedback.save()
            messages.success(request, "Feedback responded and resolved.")
        else:
            messages.error(request, "Response cannot be empty.")
    return redirect('admin_feedbacks')

@login_required
@role_required(['admin'])
def admin_add_user_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='user')
            messages.success(request, 'User added successfully.')
            return redirect('admin_users')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/admin_add_user.html', {'form': form})

@login_required
@role_required(['admin'])
def admin_add_worker_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile and ward are created inside the form.save()
            messages.success(request, 'Worker added successfully.')
            return redirect('admin_users')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/admin_add_worker.html', {'form': form})

@login_required
@role_required(['admin'])
def admin_delete_user_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')
    
    user_to_delete = get_object_or_404(User, pk=pk)
    
    # Prevent admin from deleting themselves
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_users')
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User {username} has been deleted successfully.")
        return redirect('admin_users')
    
    return render(request, 'user_dashboard/confirm_delete_user.html', {'user_to_delete': user_to_delete})

@login_required
@role_required(['admin'])
def admin_give_reward_to_least_waste_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')
    
    # Find user with least waste collected
    user_reward = Reward.objects.filter(user__profile__role='user').order_by('total_waste_collected').first()
    
    if user_reward:
        # Give bonus points (e.g., 50 points)
        bonus_points = 50
        user_reward.points += bonus_points
        user_reward.save()
        messages.success(request, f"Bonus reward of {bonus_points} points given to {user_reward.user.username} (least waste collected: {user_reward.total_waste_collected} kg).")
    else:
        messages.error(request, "No users found to give reward.")
    
    return redirect('admin_rewards')

@login_required
@role_required(['admin'])
def admin_panchayath_view(request):
    """Display and manage panchayaths"""
    panchayaths = Panchayath.objects.all().order_by('name')
    
    context = {
        'panchayaths': panchayaths,
        'page_title': 'Manage Panchayaths',
    }
    return render(request, 'user_dashboard/admin_panchayath.html', context)

@login_required
@role_required(['admin'])
def admin_add_panchayath_view(request):
    """Add a new panchayath"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name or not code:
            messages.error(request, "Please fill in all required fields.")
            return redirect('admin_add_panchayath')
        
        if Panchayath.objects.filter(name=name).exists():
            messages.error(request, f"Panchayath '{name}' already exists.")
            return redirect('admin_add_panchayath')
        
        if Panchayath.objects.filter(code=code).exists():
            messages.error(request, f"Code '{code}' is already in use.")
            return redirect('admin_add_panchayath')
        
        Panchayath.objects.create(
            name=name,
            code=code,
            description=description
        )
        messages.success(request, f"Panchayath '{name}' added successfully!")
        return redirect('admin_panchayath')
    
    context = {
        'page_title': 'Add Panchayath',
    }
    return render(request, 'user_dashboard/admin_add_panchayath.html', context)

@login_required
@role_required(['admin'])
def admin_edit_panchayath_view(request, pk):
    """Edit an existing panchayath"""
    panchayath = get_object_or_404(Panchayath, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name or not code:
            messages.error(request, "Please fill in all required fields.")
            return redirect('admin_edit_panchayath', pk=pk)
        
        # Check if name is already used by another panchayath
        if Panchayath.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, f"Panchayath '{name}' already exists.")
            return redirect('admin_edit_panchayath', pk=pk)
        
        # Check if code is already used by another panchayath
        if Panchayath.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, f"Code '{code}' is already in use.")
            return redirect('admin_edit_panchayath', pk=pk)
        
        panchayath.name = name
        panchayath.code = code
        panchayath.description = description
        panchayath.save()
        messages.success(request, f"Panchayath '{name}' updated successfully!")
        return redirect('admin_panchayath')
    
    context = {
        'panchayath': panchayath,
        'page_title': f'Edit {panchayath.name}',
    }
    return render(request, 'user_dashboard/admin_edit_panchayath.html', context)

@login_required
@role_required(['admin'])
def admin_delete_panchayath_view(request, pk):
    """Delete a panchayath"""
    panchayath = get_object_or_404(Panchayath, pk=pk)
    
    if panchayath.wards.exists():
        messages.error(request, f"Cannot delete '{panchayath.name}' as it has {panchayath.wards.count()} ward(s). Delete all wards first.")
        return redirect('admin_panchayath')
    
    panchayath_name = panchayath.name
    panchayath.delete()
    messages.success(request, f"Panchayath '{panchayath_name}' deleted successfully!")
    return redirect('admin_panchayath')

@login_required
@role_required(['admin'])
def admin_wards_management_view(request):
    """Display and manage wards"""
    wards = Ward.objects.select_related('panchayath').all().order_by('panchayath', 'ward_number')
    panchayaths = Panchayath.objects.all().order_by('name')
    
    context = {
        'wards': wards,
        'panchayaths': panchayaths,
        'page_title': 'Manage Wards',
    }
    return render(request, 'user_dashboard/admin_wards_management.html', context)

@login_required
@role_required(['admin'])
def admin_add_ward_view(request):
    """Add a new ward"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        panchayath_id = request.POST.get('panchayath')
        ward_number = request.POST.get('ward_number', '').strip()
        
        if not name or not panchayath_id or not ward_number:
            messages.error(request, "Please fill in all required fields.")
            return redirect('admin_add_ward')
        
        try:
            panchayath = Panchayath.objects.get(pk=panchayath_id)
            ward_number = int(ward_number)
        except (Panchayath.DoesNotExist, ValueError):
            messages.error(request, "Invalid panchayath or ward number.")
            return redirect('admin_add_ward')
        
        if Ward.objects.filter(panchayath=panchayath, ward_number=ward_number).exists():
            messages.error(request, f"Ward {ward_number} already exists in {panchayath.name}.")
            return redirect('admin_add_ward')
        
        Ward.objects.create(
            name=name,
            panchayath=panchayath,
            ward_number=ward_number
        )
        messages.success(request, f"Ward {ward_number} in {panchayath.name} added successfully!")
        return redirect('admin_wards_management')
    
    panchayaths = Panchayath.objects.all().order_by('name')
    context = {
        'panchayaths': panchayaths,
        'page_title': 'Add Ward',
    }
    return render(request, 'user_dashboard/admin_add_ward.html', context)

@login_required
@role_required(['admin'])
def admin_edit_ward_view(request, pk):
    """Edit an existing ward"""
    ward = get_object_or_404(Ward, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        panchayath_id = request.POST.get('panchayath')
        ward_number = request.POST.get('ward_number', '').strip()
        
        if not name or not panchayath_id or not ward_number:
            messages.error(request, "Please fill in all required fields.")
            return redirect('admin_edit_ward', pk=pk)
        
        try:
            panchayath = Panchayath.objects.get(pk=panchayath_id)
            ward_number = int(ward_number)
        except (Panchayath.DoesNotExist, ValueError):
            messages.error(request, "Invalid panchayath or ward number.")
            return redirect('admin_edit_ward', pk=pk)
        
        # Check if ward number already exists in this panchayath (excluding current ward)
        if Ward.objects.filter(panchayath=panchayath, ward_number=ward_number).exclude(pk=pk).exists():
            messages.error(request, f"Ward {ward_number} already exists in {panchayath.name}.")
            return redirect('admin_edit_ward', pk=pk)
        
        ward.name = name
        ward.panchayath = panchayath
        ward.ward_number = ward_number
        ward.save()
        messages.success(request, f"Ward updated successfully!")
        return redirect('admin_wards_management')
    
    panchayaths = Panchayath.objects.all().order_by('name')
    context = {
        'ward': ward,
        'panchayaths': panchayaths,
        'page_title': f'Edit {ward.name}',
    }
    return render(request, 'user_dashboard/admin_edit_ward.html', context)

@login_required
@role_required(['admin'])
def admin_delete_ward_view(request, pk):
    """Delete a ward"""
    ward = get_object_or_404(Ward, pk=pk)
    
    # Check if ward is assigned to any users
    if Profile.objects.filter(ward=ward).exists():
        messages.error(request, f"Cannot delete '{ward.name}' as it is assigned to {Profile.objects.filter(ward=ward).count()} user(s).")
        return redirect('admin_wards_management')
    
    ward_name = ward.name
    ward.delete()
    messages.success(request, f"Ward '{ward_name}' deleted successfully!")
    return redirect('admin_wards_management')
