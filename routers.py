from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.properties.views import RealEstateObjectViewSet

#from rest_framework.authtoken.views import obtain_auth_token
#from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#from library.views.books import BookViewSet
#from library.views.publishers import PublisherViewSet
#from library.views.users import UserLoginAPIView, RegisterUser, LogOutUser

#router = SimpleRouter()
router = DefaultRouter()
router.register('objects', RealEstateObjectViewSet, basename='real-estate-object')  # /api/v1/objects/
                                                      # /api/v1/objects/<pk>


urlpatterns = [
    # path('books/', include('library.urls.books')),
#    path('users/', include('library.urls.users')),
#    path('categories/', include('library.urls.categories')),
#    path('token-auth/', obtain_auth_token),
#    path('jwt-auth/', TokenObtainPairView.as_view()),
#    path('jwt-refresh/', TokenRefreshView.as_view()),

    # login \ logout
    # path('auth/register/', RegisterUser.as_view()),
    # path('auth/login/', UserLoginAPIView.as_view()),
    # path('auth/logout/', LogOutUser.as_view()),
] + router.urls