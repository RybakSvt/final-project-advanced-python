from datetime import date

# ============================================================================
# PROPERTIES
# ============================================================================
PROPERTY_TYPES = [
    ('apartment', 'Apartment'),
    ('studio', 'Studio'),
    ('loft', 'Loft'),
    ('duplex', 'Duplex'),
    ('penthouse', 'Penthouse'),
    ('house', 'House'),
    ('townhouse', 'Townhouse'),
    ('villa', 'Villa'),
    ('cottage', 'Cottage'),
    ('room', 'Private Room'),
    ('shared_room', 'Shared Room'),
]

PROPERTY_TYPE_GROUPS = {
    'apartments': ['apartment', 'studio', 'loft', 'duplex', 'penthouse'],
    'houses': ['house', 'townhouse', 'villa', 'cottage'],
    'rooms': ['room', 'shared_room']
}

AMENITY_CATEGORIES = [
    ('essentials', 'Essentials'),      # Wi-Fi, кухня
    ('comfort', 'Comfort'),            # кондиционер, ТВ, стиральная машина
    ('outside', 'Outside'),            # парковка, балкон, терраса, сад
    ('luxury', 'Luxury'),              # бассейн, джакузи, сауна
    ('accessibility', 'Accessibility'),# лифт, доступ для инвалидов
    ('rules', 'Rules'),                # животные, курение
]

# ============================================================================
# BOOKINGS
# ============================================================================
INFINITE_DATE = date(2999, 12, 31)

BOOKING_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]

# ============================================================================
# CURRENCIES
# ============================================================================
CURRENCY_CHOICES = [
    ('EUR', 'EUR'),
    ('USD', 'USD'),
    ('GBP', 'GBP'),
]

# ============================================================================
# REVIEWS & RATINGS
# ============================================================================
RATING_CATEGORIES = [
    ('satisfaction', 'Satisfaction'),
    ('friendliness', 'Friendliness'),
    ('reliability', 'Reliability'),
]

RATING_VALUES = [
    ('TOP', 'TOP'),
    ('OK', 'OK'),
    ('POOR', 'POOR'),
]