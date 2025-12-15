from django.db import models
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from decimal import Decimal

from django.utils.translation import gettext_lazy as _


class RealEstateObject(models.Model):

    PROPERTY_TYPE_GROUPS = {
        'apartments': ['apartment', 'studio', 'loft', 'duplex', 'penthouse'],
        'houses': ['house', 'townhouse', 'villa', 'cottage'],
        'rooms': ['room', 'shared_room']
    }


    AMENITY_CATEGORIES = {
        'essentials': ['has_wifi', 'has_kitchen', 'has_hot_water'],
        'comfort': ['has_tv', 'has_ac', 'has_washer'],
        'outside': ['has_parking', 'has_balcony'],
        'rules': ['has_pets_allowed', 'has_smoking_allowed'],
    }

    PROPERTY_TYPES = [
        ('apartment', _('Apartment')),
        ('studio', _('Studio')),
        ('loft', _('Loft')),
        ('duplex', _('Duplex')),
        ('penthouse', _('Penthouse')),
        ('house', _('House')),
        ('townhouse', _('Townhouse')),
        ('villa', _('Villa')),
        ('cottage', _('Cottage')),
        ('room', _('Private Room')),
        ('shared_room', _('Shared Room')),
    ]

    host = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='real_estate_objects',           #имя обратной связи от User к его объектам недвижимости
        verbose_name=_('Host')
    )

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    property_type = models.CharField(
        _('Property Type'),
        max_length=20,
        choices=PROPERTY_TYPES
    )

    address = models.CharField(_('Full Address'), max_length=255)
    street = models.CharField(_('Street'), max_length=255, blank=True)
    house_number = models.CharField(_('House Number'), max_length=20, blank=True)
    district = models.CharField(_('District'), max_length=100, blank=True)
    city = models.CharField(_('City'), max_length=100)
    country = models.CharField(_('Country'), max_length=100, default='Germany')
    postal_code = models.CharField(_('Postal_code'), max_length=20, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


    rooms = models.IntegerField()
    bathrooms = models.IntegerField()
    max_guests = models.IntegerField()
    area_sqm = models.IntegerField(null=True, blank=True)


    has_wifi = models.BooleanField(
        verbose_name=_('Wi-Fi'),
        default=True,
        help_text=_('Property has Wi-Fi internet access')
    )
    has_kitchen = models.BooleanField(
        verbose_name=_('Kitchen'),
        default=True,
        help_text=_('Property has a kitchen or kitchenette')
    )

    has_tv = models.BooleanField(
        verbose_name=_('TV'),
        default=True,
        help_text=_('Property has television')
    )

    has_ac = models.BooleanField(
        verbose_name=_('Air Conditioning'),
        default=False,
        help_text=_('Property has air conditioning')
    )

    has_washer = models.BooleanField(
        verbose_name=_('Washing Machine'),
        default=False,
        help_text=_('Property has a washing machine')
    )

    has_parking = models.BooleanField(
        verbose_name=_('Parking'),
        default=False,
        help_text=_('Property has parking space available')
    )
    has_balcony = models.BooleanField(
        verbose_name=_('Balcony/Terrace'),
        default=False,
        help_text=_('Property has a balcony or terrace')
    )

    has_pets_allowed = models.BooleanField(
        verbose_name=_('Pets Allowed'),
        default=False,
        help_text=_('Pets are allowed in the property')
    )
    has_smoking_allowed = models.BooleanField(
        verbose_name=_('Smoking Allowed'),
        default=False,
        help_text=_('Smoking is allowed in the property')
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} in {self.city}"

    def get_property_group(self):
        """Возвращает группу свойства (apartments/houses/rooms)"""
        for group_name, types in self.PROPERTY_TYPE_GROUPS.items():
            if self.property_type in types:
                return group_name
        return self.property_type

    def get_amenities_by_category(self):
        """Возвращает удобства по категориям"""
        amenities = {}
        for category, fields in self.AMENITY_CATEGORIES.items():
            amenities[category] = {
                field: getattr(self, field) for field in fields
            }
        return amenities

    class Meta:
        verbose_name = _('Real Estate Object')
        verbose_name_plural = _('Real Estate Objects')
        ordering = ['-created_at']


class RealEstateListing(models.Model):
    real_estate_object = models.ForeignKey(
        RealEstateObject,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name=_('Real Estate Object')
    )

    promo_title = models.CharField(
        verbose_name=_('Promo Title'),
        max_length=200,
        blank=True,
        help_text=_('Optional promotional text for special offers or discounts')
    )

    price_per_night = models.DecimalField(
        verbose_name=_('Price Per Night'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    currency = models.CharField(
        verbose_name=_('Currency'),
        max_length=3,
        default='EUR',
        choices=[('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP')]
    )

    minimum_stay = models.IntegerField(
        verbose_name=_('Minimum Stay'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Minimum number of nights required')
    )

    check_in_time = models.TimeField(
        verbose_name=_('Check-in Time'),
        default='15:00'
    )

    check_out_time = models.TimeField(
        verbose_name=_('Check-out Time'),
        default='11:00'
    )

    cancellation_days_before = models.PositiveIntegerField(
        verbose_name=_('Cancellation Days Before Check-in'),
        default=2,
        help_text=_('Guest can cancel up to this many days before check-in')
    )

    is_active = models.BooleanField(
        verbose_name=_('Is Active'),
        default=True,
        help_text=_('Show this listing in search results')
    )

    is_approved = models.BooleanField(
        verbose_name=_('Is Approved'),
        default=False,
        help_text=_('Listing has been approved by moderator')
    )

    moderation_notes = models.TextField(
        verbose_name=_('Moderation Notes'),
        blank=True,
        help_text=_('Notes from moderator (visible only to staff)')
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created At'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name=_('Updated At'),
        auto_now=True
    )

    def __str__(self):
        return f"{self.real_estate_object.title} - {self.price_per_night}{self.currency}/night"

    class Meta:
        verbose_name = _('Real Estate Listing')
        verbose_name_plural = _('Real Estate Listings')
        ordering = ['-created_at']






