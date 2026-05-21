from django import forms
from django.utils import timezone
from .models import Appointment
from doctors.models import Doctor
import datetime


def generate_slots(doctor, date):
    """
    Return a list of (time_str, label) tuples for available slots
    on the given date for the given doctor.
    Excludes already-booked slots (Pending or Approved).
    """
    if not doctor or not date:
        return []

    # Check if the date falls on an available day
    day_abbr = date.strftime('%a')  # Mon, Tue, ...
    if day_abbr not in doctor.available_days_list:
        return []

    booked_slots = set(
        Appointment.objects.filter(
            doctor=doctor,
            date=date,
            status__in=['Pending', 'Approved'],
        ).values_list('time_slot', flat=True)
    )

    slots = []
    current = datetime.datetime.combine(date, doctor.slot_start_time)
    end = datetime.datetime.combine(date, doctor.slot_end_time)
    duration = datetime.timedelta(minutes=doctor.slot_duration_minutes)
    now = datetime.datetime.now()

    while current + duration <= end:
        slot_time = current.time()
        # Skip past slots for today
        if date == timezone.localdate() and current <= now:
            current += duration
            continue
        if slot_time not in booked_slots:
            label = current.strftime('%I:%M %p')
            slots.append((slot_time.strftime('%H:%M'), label))
        current += duration

    return slots


class BookAppointmentForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(available=True),
        empty_label='-- Select a Doctor --',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor'}),
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_date',
        }),
    )
    time_slot = forms.ChoiceField(
        choices=[('', '-- Select a Time Slot --')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_time_slot'}),
    )
    patient_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your symptoms or reason for visit (optional)',
        }),
        label='Reason for Visit',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If doctor + date are submitted, populate time_slot choices dynamically
        if self.data.get('doctor') and self.data.get('date'):
            try:
                doctor = Doctor.objects.get(pk=self.data['doctor'], available=True)
                date = datetime.date.fromisoformat(self.data['date'])
                slots = generate_slots(doctor, date)
                self.fields['time_slot'].choices = [('', '-- Select a Time Slot --')] + slots
            except (Doctor.DoesNotExist, ValueError):
                pass

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.localdate():
            raise forms.ValidationError('Please choose today or a future date.')
        return date

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        date = cleaned.get('date')
        time_slot_str = cleaned.get('time_slot')

        if doctor and date and time_slot_str:
            try:
                time_slot = datetime.time.fromisoformat(time_slot_str)
            except ValueError:
                raise forms.ValidationError('Invalid time slot selected.')

            # Verify slot is still available (race-condition guard)
            conflict = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time_slot=time_slot,
                status__in=['Pending', 'Approved'],
            ).exists()
            if conflict:
                raise forms.ValidationError(
                    'This slot was just booked by someone else. Please choose another.'
                )
            cleaned['time_slot_obj'] = time_slot

        return cleaned
