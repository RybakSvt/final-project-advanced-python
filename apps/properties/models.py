from django.db import models
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.shared.constants import (
    PROPERTY_TYPES,
    PROPERTY_TYPE_GROUPS,
    CURRENCY_CHOICES,
    AMENITY_CATEGORIES
)

from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    country = models.CharField(_('Country'), max_length=100, default='Germany')
    city = models.CharField(_('City'), max_length=100)
    street = models.CharField(_('Street'), max_length=255, blank=True)
    house_number = models.CharField(_('House Number'), max_length=20, blank=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    longitude = models.FloatField(_('Longitude'), null=True, blank=True)
    is_normalized = models.BooleanField(
        _('Is Normalized'),
        default=False,
        help_text=_('Address has been processed by geocoder')
    )


    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        #unique_together = ['country', 'city', 'street', 'house_number', 'postal_code']

    def __str__(self):
        return f"{self.street} {self.house_number}, {self.city}, {self.country}"


    @property
    def full_address(self):
        parts = []
        if self.street:
            parts.append(str(self.street))
        if self.house_number:
            parts.append(str(self.house_number))
        if self.city:
            parts.append(str(self.city))
        if self.postal_code:
            parts.append(str(self.postal_code))
        if self.country:
            parts.append(str(self.country))

        return ', '.join(parts)


class Amenity(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=50,
        unique=True
    )
    category = models.CharField(
        _('Category'),
        max_length=20,
        choices=AMENITY_CATEGORIES,
        default='essentials'
    )

    class Meta:
        ordering = ['category', 'name']


class PropertyStats(models.Model):
    rooms = models.PositiveSmallIntegerField(
        _('Rooms'),
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    bathrooms = models.PositiveSmallIntegerField(
        _('Bathrooms'),
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    max_guests = models.PositiveSmallIntegerField(
        _('Max Guests'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    area_sqm = models.PositiveSmallIntegerField(
        _('Area (m²)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10000)]
    )

    class Meta:
        verbose_name = _('Property Stats')
        verbose_name_plural = _('Property Stats')

    def __str__(self):
        return f"{self.rooms} rooms, {self.area_sqm} m²"


class RealEstateObject(models.Model):
    host = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='real_estate_objects',
        verbose_name=_('Host')
    )
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    property_type = models.CharField(
        _('Property Type'),
        max_length=20,
        choices=PROPERTY_TYPES
    )

    address_raw = models.TextField(
        _('Raw Address Input'),
        blank=True,
        help_text=_('Original address entered by host (before normalization)')
    )

    address = models.ForeignKey(  # существующее поле
        Address,
        on_delete=models.PROTECT,
        related_name='properties',
        verbose_name=_('Normalized Address')
    )

    stats = models.OneToOneField(
        PropertyStats,
        on_delete=models.CASCADE,
        related_name='real_estate_object',
        verbose_name=_('Property Stats')
    )
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name='properties',
        verbose_name=_('Amenities')
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.title} in {self.address.city}"

    def get_property_group(self):
        """Возвращает группу свойства (apartments/houses/rooms)"""
        from apps.shared.constants import PROPERTY_TYPE_GROUPS
        for group_name, types in PROPERTY_TYPE_GROUPS.items():
            if self.property_type in types:
                return group_name
        return self.property_type

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
        choices=CURRENCY_CHOICES
    )

    minimum_stay = models.PositiveSmallIntegerField(
        verbose_name=_('Minimum Stay'),
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(365)
        ],
        help_text=_('Minimum number of nights required (1-365)')
    )

    check_in_time = models.TimeField(
        verbose_name=_('Check-in Time'),
        max_length=5,
        default='15:00'
    )

    check_out_time = models.TimeField(
        verbose_name=_('Check-out Time'),
        max_length=5,
        default='11:00'
    )

    cancellation_days_before = models.PositiveSmallIntegerField(
        verbose_name=_('Cancellation Days Before Check-in'),
        default=2,
        validators=[MaxValueValidator(365)],
        help_text=_('Guest can cancel up to this many days before check-in (0-365)')
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

    view_count = models.PositiveIntegerField(
        verbose_name=_('View Count'),
        default=0,
        help_text=_('Number of times this listing was viewed')
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









