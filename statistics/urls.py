from django.urls import path
from . import views


urlpatterns = [
    # Страницы (HTML)
    path('dashboard/', lambda r: render(r, 'statistics/dashboard.html'), name='stat_dashboard'),
    path('personal/', views.personal_statistics_view, name='stat_personal'),

    # API (JSON)
    path('api/statistics/dashboard/', views.dashboard_api, name='api_dashboard'),
    path('api/statistics/top-users/', views.top_users_api, name='api_top_users'),
]