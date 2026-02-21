from django.urls import path, include
from .views import MailingViewSet # Предполагаемый ViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'mailings', MailingViewSet) # Пример регистрации ViewSet

urlpatterns = [
    # Подключаем URL'ы, сгенерированные роутером
    path('', include(router.urls)),
    # path('another_mailing_url/', views.some_other_view, name='other_view'),
]