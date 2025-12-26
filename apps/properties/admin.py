from django.contrib import admin
from .models import RealEstateObject, RealEstateListing, Address, PropertyStats, Amenity


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_address', 'city', 'country']
    list_filter = ['city', 'country']
    search_fields = ['city', 'street', 'postal_code']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(PropertyStats)
class PropertyStatsAdmin(admin.ModelAdmin):
    list_display = ['id', 'rooms', 'area_sqm', 'bathrooms', 'max_guests']
    list_filter = ['rooms', 'bathrooms']


@admin.register(RealEstateObject)
class RealEstateObjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'get_city', 'property_type', 'host']
    list_filter = ['property_type', 'address__city']  # фильтр через связь
    search_fields = ['title', 'description', 'address__city', 'address__street']
    raw_id_fields = ['host', 'address', 'stats']

    def get_city(self, obj):
        return obj.address.city if obj.address else ''

    get_city.short_description = 'City'
    get_city.admin_order_field = 'address__city'


@admin.register(RealEstateListing)
class RealEstateListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_title', 'price_per_night', 'is_approved', 'is_active', 'created_at']
    list_filter = ['is_approved', 'is_active', 'currency']
    search_fields = ['real_estate_object__title', 'real_estate_object__address__city']
    raw_id_fields = ['real_estate_object']

    def get_title(self, obj):
        return obj.real_estate_object.title

    get_title.short_description = 'Title'
    get_title.admin_order_field = 'real_estate_object__title'