from django.urls import path
from .views import UsuarioCreateView, CustomTokenObtainPairView, logout_view

urlpatterns = [
    path('register/', UsuarioCreateView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
