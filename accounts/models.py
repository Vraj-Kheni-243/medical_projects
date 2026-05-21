from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PatientProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('Unknown', 'Unknown'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )
    profile_picture = models.ImageField(
        upload_to='patients/profiles/',
        blank=True,
        null=True,
    )
    phone = models.CharField(max_length=15, blank=True, default='')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        default='',
    )
    blood_group = models.CharField(
        max_length=10,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        default='Unknown',
    )
    address = models.TextField(blank=True, default='')
    emergency_contact = models.CharField(max_length=15, blank=True, default='')
    allergies = models.TextField(
        blank=True,
        default='',
        help_text='List any known allergies.',
    )
    medical_notes = models.TextField(
        blank=True,
        default='',
        help_text='Any existing conditions or notes for doctors.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from django.utils import timezone
        today = timezone.localdate()
        dob = self.date_of_birth
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )


@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    """Auto-create a PatientProfile whenever a new User is registered."""
    if created:
        # Only create for non-doctor users; doctors get their own model
        PatientProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_patient_profile(sender, instance, **kwargs):
    if hasattr(instance, 'patient_profile'):
        instance.patient_profile.save()
