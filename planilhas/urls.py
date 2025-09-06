from django.urls import path
from .views import exportar_produtos_csv
from .importacao import importar_produtos_csv

urlpatterns = [
    path('exportar-produtos/', exportar_produtos_csv, name='exportar-produtos-csv'),
    path('importar-produtos/', importar_produtos_csv, name='importar-produtos-csv'),
]
