from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# REST API router
router = DefaultRouter()
router.register(r'projects', views.CIHRProjectViewSet)

app_name = 'tracker'

urlpatterns = [
    # Web interface
    path('', views.home, name='home'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<str:project_id>/', views.project_detail, name='project_detail'),
    path('statistics/', views.statistics, name='statistics'),
    path('institutions/', views.institutions, name='institutions'),
    path('cihr-institutes/', views.cihr_institutes, name='cihr_institutes'),
    
    # AJAX endpoints
    path('api/search/', views.api_project_search, name='api_search'),
    
    # REST API
    path('api/', include(router.urls)),
] 