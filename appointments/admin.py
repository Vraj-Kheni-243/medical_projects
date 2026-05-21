from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time_slot', 'status', 'reject_reason', 'created_at')
    list_filter = ('status', 'doctor', 'date')
    search_fields = ('patient__username', 'patient__email', 'doctor__user__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
