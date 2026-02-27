from django.urls import path
from . import views


urlpatterns = [
    # Страницы (HTML)
    path('dashboard/', lambda r: render(r, 'my_statistics/dashboard.html'), name='stat_dashboard'),
    path('personal/', views.personal_statistics_view, name='stat_personal'),

    # API (JSON)
    path('api/my_statistics/dashboard/', views.dashboard_api, name='api_dashboard'),
    path('api/my_statistics/top-users/', views.top_users_api, name='api_top_users'),
]