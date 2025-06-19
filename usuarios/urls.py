from django.urls import path
from .views import UsuarioCreateView, CustomTokenObtainPairView

urlpatterns = [
    path('register/', UsuarioCreateView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
]
