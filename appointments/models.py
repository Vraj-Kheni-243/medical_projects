from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from doctors.models import Doctor


class Appointment(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    REJECT_REASONS = [
        ('Not Available', 'Doctor not available'),
        ('Emergency', 'Doctor in emergency'),
        ('Time Conflict', 'Time conflict'),
        ('Invalid Details', 'Invalid patient details'),
        ('Clinic Closed', 'Clinic closed'),
        ('Other', 'Other'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    date = models.DateField()
    time_slot = models.TimeField(
        help_text='Appointment start time (HH:MM).',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending',
    )
    reject_reason = models.CharField(
        max_length=50,
        choices=REJECT_REASONS,
        blank=True,
        null=True,
    )
    patient_notes = models.TextField(
        blank=True,
        default='',
        help_text='Reason for visit / symptoms described by patient.',
    )
    doctor_notes = models.TextField(
        blank=True,
        default='',
        help_text='Doctor notes after consultation.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Prevent double-booking the same doctor slot."""
        if self.date and self.time_slot and self.doctor_id:
            conflict_qs = Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time_slot=self.time_slot,
                status__in=['Pending', 'Approved'],
            )
            if self.pk:
                conflict_qs = conflict_qs.exclude(pk=self.pk)
            if conflict_qs.exists():
                raise ValidationError(
                    'This time slot is already booked for the selected doctor. '
                    'Please choose a different slot.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_past(self):
        from datetime import datetime, time as dt_time
        import datetime as dt_module
        slot_dt = dt_module.datetime.combine(self.date, self.time_slot)
        return slot_dt < dt_module.datetime.now()

    def __str__(self):
        return (
            f"{self.patient.username} → Dr. {self.doctor.display_name} "
            f"on {self.date} at {self.time_slot.strftime('%I:%M %p')} [{self.status}]"
        )

    class Meta:
        ordering = ['-date', '-time_slot', '-id']
        # DB-level uniqueness: one patient per slot per doctor
        unique_together = [('doctor', 'date', 'time_slot', 'patient')]
