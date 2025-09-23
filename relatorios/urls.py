from django.urls import path
from .views import RelatorioHTMLView

urlpatterns = [
    path('conta/html/', RelatorioHTMLView.as_view(), name='relatorio-conta-html'),
]


