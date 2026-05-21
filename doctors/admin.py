from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'specialization', 'experience_years', 'consultation_fee', 'rating', 'available')
    list_filter = ('available', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    list_editable = ('available', 'rating')
    fieldsets = (
        ('Account', {'fields': ('user', 'available')}),
        ('Professional Info', {'fields': ('specialization', 'bio', 'experience_years', 'consultation_fee', 'rating', 'profile_picture')}),
        ('Availability Schedule', {'fields': ('available_days', 'slot_start_time', 'slot_end_time', 'slot_duration_minutes')}),
    )


admin.site.site_header = 'VRAJ Care Admin'
admin.site.site_title = 'VRAJ Care Portal'
admin.site.index_title = 'Welcome to VRAJ Care Admin Panel'
