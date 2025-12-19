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

AMENITY_CATEGORIES = {
    'essentials': ['has_wifi', 'has_kitchen', 'has_hot_water'],
    'comfort': ['has_tv', 'has_ac', 'has_washer'],
    'outside': ['has_parking', 'has_balcony'],
    'rules': ['has_pets_allowed', 'has_smoking_allowed'],
}

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