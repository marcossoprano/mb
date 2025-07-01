from django.urls import path
from .views import UsuarioCreateView, CustomTokenObtainPairView, logout_view, trocar_senha_view, deletar_conta_view

urlpatterns = [
    path('register/', UsuarioCreateView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('trocar-senha/', trocar_senha_view, name='trocar-senha'),
    path('deletar-conta/', deletar_conta_view, name='deletar-conta'),
]
