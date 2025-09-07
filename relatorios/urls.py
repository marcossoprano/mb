from django.urls import path
from .views import RelatorioPDFView

urlpatterns = [
    path('conta/pdf/', RelatorioPDFView.as_view(), name='relatorio-conta-pdf'),
]


