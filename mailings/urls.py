from django.urls import path
from . import views


app_name = 'mailings'

urlpatterns = [
    # URL-адреса для предствлений рассылок
    path('mailings/', views.mailing_list, name='mailing_list'),       # /mail/mailings/
    path('mailings/<int:pk>/', views.mailing_detail, name='mailing_detail'), # /mail/mailings/1/
    path('mailings/create/', views.MailingCreateView.as_view(), name='mailing_create'), # /mail/mailings/create/
]