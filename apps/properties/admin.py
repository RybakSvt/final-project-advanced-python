from django.contrib import admin
from .models import RealEstateObject, RealEstateListing

@admin.register(RealEstateObject)
class RealEstateObjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'city', 'property_type']
    list_filter = ['property_type', 'city']
    search_fields = ['title', 'city', 'description']
    raw_id_fields = ['host']

@admin.register(RealEstateListing)
class RealEstateListingAdmin(admin.ModelAdmin):
    list_display = ['real_estate_object', 'price_per_night', 'is_approved', 'created_at', 'is_active']
    list_filter = ['is_approved', 'created_at', 'is_active']
    search_fields = ['real_estate_object__title', 'real_estate_object__city']
    raw_id_fields = ['real_estate_object']
