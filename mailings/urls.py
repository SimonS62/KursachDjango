from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, MessageViewSet, MailingViewSet, MessageAttemptViewSet, DashboardView


router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'mailings', MailingViewSet, basename='mailing')
router.register(r'attempts', MessageAttemptViewSet, basename='messageattempt') # ReadOnly

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'), # URL для главной страницы
    # URL для запуска рассылки уже встроен в MailingViewSet как /api/mailings/<pk>/trigger-send/
]
