from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import json

from .models import CIHRProject
from .serializers import CIHRProjectSerializer, CIHRProjectListSerializer


def home(request):
    """Home page with overview statistics"""
    context = {
        'page_title': 'CIHR Projects Tracker',
        'page_description': 'Comprehensive database of Canadian Institutes of Health Research funded projects',
        'page_icon': 'fas fa-flag',
        'total_projects': CIHRProject.objects.count(),
        'broad_study_types': CIHRProject.objects.values('broad_study_type').annotate(count=Count('broad_study_type')).order_by('-count'),
        'therapeutic_areas': CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').values('therapeutic_area').annotate(count=Count('therapeutic_area')).order_by('-count')[:10],
        'primary_institutes': CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').values('primary_institute').annotate(count=Count('primary_institute')).order_by('-count')[:5],
    }
    return render(request, 'tracker/home.html', context)


def project_list(request):
    """Project list with filtering and pagination"""
    projects = CIHRProject.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(project_title__icontains=search_query) |
            Q(abstract_summary__icontains=search_query) |
            Q(keywords__icontains=search_query) |
            Q(principal_investigators__icontains=search_query)
        )
    
    # Filtering
    broad_study_type = request.GET.get('broad_study_type', '')
    if broad_study_type:
        projects = projects.filter(broad_study_type=broad_study_type)
    
    therapeutic_area = request.GET.get('therapeutic_area', '')
    if therapeutic_area:
        projects = projects.filter(therapeutic_area__icontains=therapeutic_area)
    
    primary_institute = request.GET.get('primary_institute', '')
    if primary_institute:
        projects = projects.filter(primary_institute=primary_institute)
    
    primary_theme = request.GET.get('primary_theme', '')
    if primary_theme:
        projects = projects.filter(primary_theme=primary_theme)
    
    competition_year = request.GET.get('competition_year', '')
    if competition_year:
        projects = projects.filter(competition_year_month__startswith=competition_year)
    
    # Ordering
    order_by = request.GET.get('order_by', '-project_id')
    projects = projects.order_by(order_by)
    
    # Pagination
    paginator = Paginator(projects, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    filter_options = {
        'broad_study_types': CIHRProject.objects.values_list('broad_study_type', flat=True).distinct(),
        'therapeutic_areas': CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').values_list('therapeutic_area', flat=True).distinct()[:20],
        'primary_institutes': CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').values_list('primary_institute', flat=True).distinct(),
        'primary_themes': CIHRProject.objects.exclude(primary_theme__isnull=True).exclude(primary_theme='').values_list('primary_theme', flat=True).distinct(),
        'competition_years': sorted(set([year[:4] for year in CIHRProject.objects.exclude(competition_year_month__isnull=True).values_list('competition_year_month', flat=True) if year]), reverse=True),
    }
    
    context = {
        'page_title': 'CIHR Projects',
        'page_description': f'Browse {projects.count()} CIHR-funded research projects',
        'page_icon': 'fas fa-list',
        'show_breadcrumb': True,
        'page_obj': page_obj,
        'search_query': search_query,
        'current_filters': {
            'broad_study_type': broad_study_type,
            'therapeutic_area': therapeutic_area,
            'primary_institute': primary_institute,
            'primary_theme': primary_theme,
            'competition_year': competition_year,
        },
        'filter_options': filter_options,
        'total_results': projects.count(),
    }
    return render(request, 'tracker/project_list.html', context)


def project_detail(request, project_id):
    """Project detail page showing only 'yes' fields"""
    project = get_object_or_404(CIHRProject, project_id=project_id)
    
    # Get only fields with 'yes' values
    yes_fields = project.get_yes_fields()
    
    context = {
        'page_title': f'Project {project.project_id}',
        'page_description': project.project_title,
        'page_icon': 'fas fa-file-alt',
        'show_breadcrumb': True,
        'project': project,
        'yes_fields': yes_fields,
    }
    return render(request, 'tracker/project_detail.html', context)


def statistics(request):
    """Statistics and analytics page"""
    # Basic statistics
    total_projects = CIHRProject.objects.count()
    
    # Study type distribution
    study_types = CIHRProject.objects.values('broad_study_type').annotate(count=Count('broad_study_type')).order_by('-count')
    
    # Therapeutic area distribution
    therapeutic_areas = CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').values('therapeutic_area').annotate(count=Count('therapeutic_area')).order_by('-count')[:15]
    
    # Institute distribution
    institutes = CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').values('primary_institute').annotate(count=Count('primary_institute')).order_by('-count')[:10]
    
    # Theme distribution
    themes = CIHRProject.objects.exclude(primary_theme__isnull=True).exclude(primary_theme='').values('primary_theme').annotate(count=Count('primary_theme')).order_by('-count')[:10]
    
    # Year distribution
    year_distribution = {}
    for project in CIHRProject.objects.exclude(competition_year_month__isnull=True):
        year = project.competition_year_month[:4] if project.competition_year_month else 'Unknown'
        year_distribution[year] = year_distribution.get(year, 0) + 1
    
    # Technology adoption
    tech_fields = [
        'ai_machine_learning', 'digital_health', 'telemedicine', 'wearable_technology',
        'big_data_analytics', 'blockchain'
    ]
    tech_stats = {}
    for field in tech_fields:
        tech_stats[field] = CIHRProject.objects.filter(**{field: 'yes'}).count()
    
    # Special focus areas
    focus_areas = {
        'Patient Engagement': CIHRProject.objects.filter(patient_engagement='yes').count(),
        'Indigenous Collaboration': CIHRProject.objects.filter(indigenous_collaboration='yes').count(),
        'International Collaboration': CIHRProject.objects.filter(international_collaboration='yes').count(),
        'Health Equity': CIHRProject.objects.filter(health_equity='yes').count(),
        'Implementation Science': CIHRProject.objects.filter(implementation_science='yes').count(),
        'Knowledge Translation': CIHRProject.objects.filter(knowledge_translation_focus='yes').count(),
    }
    
    context = {
        'page_title': 'Statistics & Analytics',
        'page_description': 'Comprehensive statistics and visualizations of CIHR projects',
        'page_icon': 'fas fa-chart-bar',
        'show_breadcrumb': True,
        'total_projects': total_projects,
        'study_types': study_types,
        'therapeutic_areas': therapeutic_areas,
        'institutes': institutes,
        'themes': themes,
        'year_distribution': dict(sorted(year_distribution.items())),
        'tech_stats': tech_stats,
        'focus_areas': focus_areas,
    }
    return render(request, 'tracker/statistics.html', context)


def api_project_search(request):
    """AJAX endpoint for project search suggestions"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    projects = CIHRProject.objects.filter(
        Q(project_title__icontains=query) |
        Q(principal_investigators__icontains=query)
    )[:10]
    
    results = []
    for project in projects:
        results.append({
            'id': project.project_id,
            'title': project.project_title,
            'pi': project.principal_investigators,
            'url': project.get_absolute_url(),
        })
    
    return JsonResponse({'results': results})


# REST API ViewSets
class CIHRProjectViewSet(viewsets.ModelViewSet):
    """REST API ViewSet for CIHR projects"""
    queryset = CIHRProject.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['project_title', 'abstract_summary', 'keywords', 'principal_investigators']
    filterset_fields = ['broad_study_type', 'therapeutic_area', 'primary_institute', 'primary_theme']
    ordering_fields = ['project_id', 'project_title', 'competition_year_month']
    ordering = ['-project_id']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CIHRProjectListSerializer
        return CIHRProjectSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """API endpoint for statistics"""
        total = self.get_queryset().count()
        study_types = self.get_queryset().values('broad_study_type').annotate(count=Count('broad_study_type'))
        
        return Response({
            'total_projects': total,
            'study_type_distribution': list(study_types)
        })
    
    @action(detail=True, methods=['get'])
    def yes_fields(self, request, pk=None):
        """API endpoint for project's 'yes' fields"""
        project = self.get_object()
        return Response(project.get_yes_fields())
