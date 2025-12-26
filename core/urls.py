"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
#from drf_yasg.views import get_schema_view
#from drf_yasg import openapi
#from rest_framework.permissions import IsAuthenticated

#schema_view = get_schema_view(
#     openapi.Info(
#         title='Library Swagger',
#         default_version='1.0.0',
#         description='TEST DESCRIPTION',
#         terms_of_service='https://policies.google.com/terms?hl=en-US',
#         contact=openapi.Contact(name='Vladislav', email='test.gmail@gmail.com'),
#         license=openapi.License(name='AWESOME LICENSE')
#     ),
#     public=True,
#     # permission_classes=[IsAuthenticated]
# )


urlpatterns = [
    path('admin/', admin.site.urls),      # http://127.0.0.1:8000/admin/
    path('api/v1/', include('routers')),  # http://127.0.0.1:8000/api/v1/

#     # SWAGGER
#     path(
#         'swagger/',
#         schema_view.with_ui('swagger')
#     ),  # http://127.0.0.1:8000/api/v1/
#     path(
#         'redoc/',
#         schema_view.with_ui('redoc')
#     ),  # http://127.0.0.1:8000/api/v1/
 ]
