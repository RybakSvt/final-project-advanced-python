from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.properties.views import (
    RealEstateObjectViewSet,
    PublicListingViewSet,
    HostListingViewSet,
    ListingDetailViewSet,
)

#from rest_framework.authtoken.views import obtain_auth_token
#from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#router = SimpleRouter()
router = DefaultRouter()
router.register('objects', RealEstateObjectViewSet, basename='real-estate-object')  # /api/v1/objects/
                                                                                           # /api/v1/objects/<pk>
router.register('listings', PublicListingViewSet, basename='public-listings')       # /api/v1/listings/
router.register('listing', ListingDetailViewSet, basename='listing-detail')         # /api/v1/listing/<pk>
router.register('host-listings', HostListingViewSet, basename='host-listings')       # /api/v1/host-listings
                                                                                            #/api/v1/host-listings/<id>/



urlpatterns = [
#    path('token-auth/', obtain_auth_token),
#    path('jwt-auth/', TokenObtainPairView.as_view()),
#    path('jwt-refresh/', TokenRefreshView.as_view()),

    # login \ logout
    # path('auth/register/', RegisterUser.as_view()),
    # path('auth/login/', UserLoginAPIView.as_view()),
    # path('auth/logout/', LogOutUser.as_view()),
] + router.urls