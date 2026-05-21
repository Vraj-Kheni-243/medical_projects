from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('General Physician', 'General Physician'),
        ('Cardiologist', 'Cardiologist'),
        ('Dermatologist', 'Dermatologist'),
        ('Neurologist', 'Neurologist'),
        ('Orthopedic', 'Orthopedic'),
        ('Pediatrician', 'Pediatrician'),
        ('Psychiatrist', 'Psychiatrist'),
        ('Gynecologist', 'Gynecologist'),
        ('ENT Specialist', 'ENT Specialist'),
        ('Ophthalmologist', 'Ophthalmologist'),
        ('Dentist', 'Dentist'),
        ('Urologist', 'Urologist'),
        ('Oncologist', 'Oncologist'),
        ('Endocrinologist', 'Endocrinologist'),
        ('Gastroenterologist', 'Gastroenterologist'),
        ('Pulmonologist', 'Pulmonologist'),
        ('Rheumatologist', 'Rheumatologist'),
        ('Nephrologist', 'Nephrologist'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(
        max_length=100,
        choices=SPECIALIZATION_CHOICES,
        default='General Physician',
    )
    available = models.BooleanField(default=True)

    # Extended fields
    profile_picture = models.ImageField(
        upload_to='doctors/profiles/',
        blank=True,
        null=True,
    )
    bio = models.TextField(
        blank=True,
        default='',
        help_text='Short professional biography shown to patients.',
    )
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text='Years of professional experience.',
    )
    consultation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text='Consultation fee in INR.',
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Average rating out of 5.',
    )
    # Availability schedule
    available_days = models.CharField(
        max_length=50,
        default='Mon,Tue,Wed,Thu,Fri',
        help_text='Comma-separated day abbreviations: Mon,Tue,Wed,Thu,Fri,Sat,Sun',
    )
    slot_start_time = models.TimeField(
        default='09:00',
        help_text='Start time for appointment slots (HH:MM).',
    )
    slot_end_time = models.TimeField(
        default='17:00',
        help_text='End time for appointment slots (HH:MM).',
    )
    slot_duration_minutes = models.PositiveSmallIntegerField(
        default=30,
        help_text='Duration of each appointment slot in minutes.',
    )

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def available_days_list(self):
        return [d.strip() for d in self.available_days.split(',') if d.strip()]

    def __str__(self):
        return f"Dr. {self.display_name} ({self.specialization})"

    class Meta:
        ordering = ['-rating', 'user__first_name']
