from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Doctor
from appointments.models import Appointment


def _doctor_label(doctor):
    return doctor.user.get_full_name() or doctor.user.username


# ─── DOCTOR LOGIN ─────────────────────────────────────────────────────────────
def doctor_login(request):
    if request.user.is_authenticated:
        if Doctor.objects.filter(user=request.user).exists():
            return redirect('doctor_dashboard')
        messages.error(request, 'You are logged in as a patient. Please logout first.')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if Doctor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('doctor_dashboard')
            messages.error(request, 'You are not registered as a doctor.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'doctors/login.html')


# ─── DOCTOR DASHBOARD ─────────────────────────────────────────────────────────
@login_required
def doctor_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    today = timezone.localdate()

    all_appointments = (
        Appointment.objects
        .filter(doctor=doctor)
        .select_related('patient', 'patient__patient_profile')
        .order_by('-date', '-time_slot')
    )

    today_appointments = all_appointments.filter(date=today)
    upcoming = all_appointments.filter(date__gte=today, status__in=['Pending', 'Approved'])
    pending = all_appointments.filter(status='Pending')
    approved = all_appointments.filter(status='Approved')
    rejected = all_appointments.filter(status='Rejected')

    return render(request, 'doctors/dashboard.html', {
        'doctor': doctor,
        'all_appointments': all_appointments,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming,
        'pending_appointments': pending,
        'approved_appointments': approved,
        'rejected_appointments': rejected,
        'pending_count': pending.count(),
        'approved_count': approved.count(),
        'rejected_count': rejected.count(),
        'today_count': today_appointments.count(),
        'total_count': all_appointments.count(),
        'reject_reasons': Appointment.REJECT_REASONS,
    })


# ─── APPROVE ──────────────────────────────────────────────────────────────────
@require_POST
@login_required
def approve_appointment(request, id):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, id=id, doctor=doctor)
    appointment.status = 'Approved'
    appointment.reject_reason = ''
    appointment.save()
    if appointment.patient.email:
        send_mail(
            'Appointment approved — VRAJ Care',
            (
                f'Hi {appointment.patient.get_full_name() or appointment.patient.username},\n\n'
                f'Your appointment with Dr. {_doctor_label(doctor)} '
                f'on {appointment.date} at {appointment.time_slot.strftime("%I:%M %p")} '
                f'has been approved.\n\nVRAJ Care'
            ),
            None,
            [appointment.patient.email],
            fail_silently=True,
        )
    messages.success(request, 'Appointment approved.')
    return redirect('doctor_dashboard')


# ─── REJECT ───────────────────────────────────────────────────────────────────
@require_POST
@login_required
def reject_appointment(request, id):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, id=id, doctor=doctor)
    reason = request.POST.get('reason', '')
    if reason not in dict(Appointment.REJECT_REASONS):
        messages.error(request, 'Please choose a valid rejection reason.')
        return redirect('doctor_dashboard')
    appointment.status = 'Rejected'
    appointment.reject_reason = reason
    appointment.save()
    if appointment.patient.email:
        send_mail(
            'Appointment rejected — VRAJ Care',
            (
                f'Hi {appointment.patient.get_full_name() or appointment.patient.username},\n\n'
                f'Your appointment with Dr. {_doctor_label(doctor)} '
                f'on {appointment.date} at {appointment.time_slot.strftime("%I:%M %p")} '
                f'was rejected.\nReason: {appointment.get_reject_reason_display()}\n\nVRAJ Care'
            ),
            None,
            [appointment.patient.email],
            fail_silently=True,
        )
    messages.success(request, 'Appointment rejected.')
    return redirect('doctor_dashboard')


# ─── DOCTOR LOGOUT ────────────────────────────────────────────────────────────
def doctor_logout(request):
    logout(request)
    request.session.flush()
    return redirect('/')
