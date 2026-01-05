from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.properties.views import (
    RealEstateObjectViewSet,
    PublicListingViewSet,
    HostListingViewSet,
    ListingDetailViewSet,
)

from apps.bookings.views import (
    BookingViewSet,
    HostBookingViewSet,
    CalendarViewSet,
    AvailabilityViewSet,
)

from apps.users.views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    BecomeHostView
)

from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('objects', RealEstateObjectViewSet, basename='real-estate-object')  # /api/v1/objects/
                                                                                           # /api/v1/objects/<pk>
router.register('listings', PublicListingViewSet, basename='public-listings')       # /api/v1/listings/
router.register('listing', ListingDetailViewSet, basename='listing-detail')         # /api/v1/listing/<pk>
router.register('host-listings', HostListingViewSet, basename='host-listings')       # /api/v1/host-listings
                                                                                            #/api/v1/host-listings/<id>/
router.register('bookings', BookingViewSet, basename='bookings')
router.register('host-bookings', HostBookingViewSet, basename='host-bookings')
router.register('availability', AvailabilityViewSet, basename='availability')

calendar_list = CalendarViewSet.as_view({'get': 'list'})


urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/become-host/', BecomeHostView.as_view(), name='become-host'),

    path('calendar/<int:listing_id>/', calendar_list, name='calendar'),
] + router.urls