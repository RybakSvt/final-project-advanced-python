from django.contrib import admin
from .models import Availability, Booking


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'start_date', 'end_date_display', 'created_at']
    list_filter = ['listing', 'start_date']
    search_fields = ['listing__real_estate_object__title']

    def end_date_display(self, obj):
        return "∞" if obj.is_infinite else obj.end_date

    end_date_display.short_description = 'End Date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'listing', 'check_in', 'check_out',
                    'status', 'total_price', 'created_at']
    list_filter = ['status', 'check_in', 'listing']
    search_fields = ['guest__email', 'guest__username',
                     'listing__real_estate_object__title']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['confirm_selected', 'cancel_selected']

    def confirm_selected(self, request, queryset):
        updated = 0
        for booking in queryset.filter(status='pending'):
            success, _ = booking.confirm()
            if success:
                updated += 1
        self.message_user(request, f'{updated} bookings confirmed.')

    confirm_selected.short_description = "Confirm selected bookings"

    def cancel_selected(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'{queryset.count()} bookings cancelled.')

    cancel_selected.short_description = "Cancel selected bookings"
