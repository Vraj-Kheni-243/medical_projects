import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from doctors.models import Doctor
from .forms import BookAppointmentForm, generate_slots
from .models import Appointment


def _doctor_label(doctor):
    return doctor.user.get_full_name() or doctor.user.username


def _send_appointment_email(subject, message, recipient):
    if recipient:
        send_mail(subject, message, None, [recipient], fail_silently=True)


# ─── AJAX: available slots for a doctor+date ────────────────────────────────
@require_GET
@login_required
def available_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    try:
        doctor = Doctor.objects.get(pk=doctor_id, available=True)
        date = datetime.date.fromisoformat(date_str)
    except (Doctor.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'slots': []})

    slots = generate_slots(doctor, date)
    return JsonResponse({'slots': [{'value': v, 'label': l} for v, l in slots]})


# ─── BOOK APPOINTMENT ────────────────────────────────────────────────────────
@login_required
def book_appointment(request):
    doctors = Doctor.objects.filter(available=True).select_related('user')

    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['date']
            time_slot = form.cleaned_data['time_slot_obj']
            patient_notes = form.cleaned_data.get('patient_notes', '')

            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                date=date,
                time_slot=time_slot,
                patient_notes=patient_notes,
            )
            _send_appointment_email(
                'Appointment request received — VRAJ Care',
                (
                    f'Hi {request.user.get_full_name() or request.user.username},\n\n'
                    f'Your appointment request with Dr. {_doctor_label(doctor)} '
                    f'on {appointment.date} at {appointment.time_slot.strftime("%I:%M %p")} '
                    f'is pending approval.\n\nVRAJ Care'
                ),
                request.user.email,
            )
            messages.success(request, 'Appointment requested successfully.')
            return redirect('patient_dashboard')
        # form invalid — fall through to re-render with errors
    else:
        form = BookAppointmentForm()

    return render(request, 'appointments/book.html', {
        'form': form,
        'doctors': doctors,
    })


# ─── MY APPOINTMENTS (patient) ───────────────────────────────────────────────
@login_required
def my_appointments(request):
    appointments = (
        Appointment.objects
        .filter(patient=request.user)
        .select_related('doctor__user')
    )
    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
    })


# ─── DOCTOR APPOINTMENTS LIST ────────────────────────────────────────────────
@login_required
def doctor_appointments(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointments = (
        Appointment.objects
        .filter(doctor=doctor)
        .select_related('patient')
    )
    return render(request, 'appointments/doctor_appointments.html', {
        'appointments': appointments,
    })


# ─── UPDATE STATUS (approve / reject) ────────────────────────────────────────
@require_POST
@login_required
def update_appointment_status(request, pk, status):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)

    if status not in dict(Appointment.STATUS_CHOICES):
        messages.error(request, 'Invalid appointment status.')
        return redirect('doctor_dashboard')

    appointment.status = status
    if status != 'Rejected':
        appointment.reject_reason = ''
    appointment.save()

    _send_appointment_email(
        f'Appointment {status.lower()} — VRAJ Care',
        (
            f'Your appointment with Dr. {_doctor_label(doctor)} '
            f'on {appointment.date} at {appointment.time_slot.strftime("%I:%M %p")} '
            f'was {status.lower()}.'
        ),
        appointment.patient.email,
    )
    messages.success(request, f'Appointment marked as {status.lower()}.')
    return redirect('doctor_dashboard')


# ─── CANCEL APPOINTMENT (patient) ────────────────────────────────────────────
@require_POST
@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(
        Appointment, pk=pk, patient=request.user, status='Pending'
    )
    appointment.status = 'Cancelled'
    appointment.save()
    messages.success(request, 'Appointment cancelled.')
    return redirect('patient_dashboard')


# ─── ADD DOCTOR NOTES ────────────────────────────────────────────────────────
@require_POST
@login_required
def add_doctor_notes(request, pk):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    appointment.doctor_notes = request.POST.get('doctor_notes', '').strip()
    appointment.save()
    messages.success(request, 'Notes saved.')
    return redirect('doctor_dashboard')
