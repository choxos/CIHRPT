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
        'therapeutic_areas': CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').exclude(therapeutic_area__iexact='N/A').values('therapeutic_area').annotate(count=Count('therapeutic_area')).order_by('-count')[:10],
        'primary_institutes': CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').exclude(primary_institute__iexact='N/A').values('primary_institute').annotate(count=Count('primary_institute')).order_by('-count')[:5],
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
        'therapeutic_areas': CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').exclude(therapeutic_area__iexact='N/A').values_list('therapeutic_area', flat=True).distinct()[:20],
        'primary_institutes': CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').exclude(primary_institute__iexact='N/A').values_list('primary_institute', flat=True).distinct(),
        'primary_themes': CIHRProject.objects.exclude(primary_theme__isnull=True).exclude(primary_theme='').exclude(primary_theme__iexact='N/A').values_list('primary_theme', flat=True).distinct(),
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
    
    def parse_funding_amount(amount_str):
        """Parse funding amount string to float"""
        if not amount_str:
            return 0
        # Remove $, commas, and convert to float
        try:
            return float(amount_str.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return 0
    
    # Basic statistics
    total_projects = CIHRProject.objects.count()
    
    # Study type distribution
    study_types = CIHRProject.objects.values('broad_study_type').annotate(count=Count('broad_study_type')).order_by('-count')
    
    # Therapeutic area distribution
    therapeutic_areas = CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').exclude(therapeutic_area__iexact='N/A').values('therapeutic_area').annotate(count=Count('therapeutic_area')).order_by('-count')[:15]
    
    # Institute distribution
    institutes = CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').exclude(primary_institute__iexact='N/A').values('primary_institute').annotate(count=Count('primary_institute')).order_by('-count')[:10]
    
    # Theme distribution
    themes = CIHRProject.objects.exclude(primary_theme__isnull=True).exclude(primary_theme='').exclude(primary_theme__iexact='N/A').values('primary_theme').annotate(count=Count('primary_theme')).order_by('-count')[:10]
    
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
    
    # FUNDING ANALYSIS
    
    # Calculate total funding
    total_funding = 0
    funding_projects = 0
    for project in CIHRProject.objects.exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
        amount = parse_funding_amount(project.cihr_amounts)
        if amount > 0:
            total_funding += amount
            funding_projects += 1
    
    # Funding by therapeutic area
    funding_by_therapeutic_area = {}
    for project in CIHRProject.objects.exclude(therapeutic_area__isnull=True).exclude(therapeutic_area='').exclude(therapeutic_area__iexact='N/A').exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
        area = project.therapeutic_area
        amount = parse_funding_amount(project.cihr_amounts)
        if amount > 0:
            funding_by_therapeutic_area[area] = funding_by_therapeutic_area.get(area, 0) + amount
    
    # Top 10 funded therapeutic areas
    top_funded_areas = sorted(funding_by_therapeutic_area.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Funding by CIHR institute
    funding_by_institute = {}
    for project in CIHRProject.objects.exclude(primary_institute__isnull=True).exclude(primary_institute='').exclude(primary_institute__iexact='N/A').exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
        institute = project.primary_institute
        amount = parse_funding_amount(project.cihr_amounts)
        if amount > 0:
            funding_by_institute[institute] = funding_by_institute.get(institute, 0) + amount
    
    # Top 10 funded institutes
    top_funded_institutes = sorted(funding_by_institute.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Funding by study type
    funding_by_study_type = {}
    for project in CIHRProject.objects.exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
        study_type = project.broad_study_type
        amount = parse_funding_amount(project.cihr_amounts)
        if amount > 0:
            funding_by_study_type[study_type] = funding_by_study_type.get(study_type, 0) + amount
    
    # Funding by research theme
    funding_by_theme = {}
    for project in CIHRProject.objects.exclude(primary_theme__isnull=True).exclude(primary_theme='').exclude(primary_theme__iexact='N/A').exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
        theme = project.primary_theme
        amount = parse_funding_amount(project.cihr_amounts)
        if amount > 0:
            funding_by_theme[theme] = funding_by_theme.get(theme, 0) + amount
    
    # Top 10 funded themes
    top_funded_themes = sorted(funding_by_theme.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Funding by special focus areas
    funding_by_focus = {}
    focus_area_fields = {
        'Patient Engagement': 'patient_engagement',
        'Indigenous Collaboration': 'indigenous_collaboration', 
        'International Collaboration': 'international_collaboration',
        'Health Equity': 'health_equity',
        'Implementation Science': 'implementation_science',
        'Knowledge Translation': 'knowledge_translation_focus',
    }
    
    for area_name, field_name in focus_area_fields.items():
        total_funding_area = 0
        for project in CIHRProject.objects.filter(**{field_name: 'yes'}).exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
            amount = parse_funding_amount(project.cihr_amounts)
            total_funding_area += amount
        funding_by_focus[area_name] = total_funding_area
    
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
        # Funding data
        'total_funding': total_funding,
        'funding_projects': funding_projects,
        'top_funded_areas': top_funded_areas,
        'top_funded_institutes': top_funded_institutes,
        'funding_by_study_type': funding_by_study_type,
        'top_funded_themes': top_funded_themes,
        'funding_by_focus': funding_by_focus,
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


def institutions(request):
    """Research institutions page showing all institutions with project counts"""
    # Get all research institutions with project counts
    institutions_data = CIHRProject.objects.exclude(
        research_institution__isnull=True
    ).exclude(
        research_institution=''
    ).exclude(
        research_institution__iexact='N/A'
    ).values('research_institution').annotate(
        project_count=Count('research_institution')
    ).order_by('-project_count')
    
    # Calculate total funding by institution
    for institution in institutions_data:
        total_funding = 0
        funding_count = 0
        for project in CIHRProject.objects.filter(research_institution=institution['research_institution']).exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
            try:
                amount = float(project.cihr_amounts.replace('$', '').replace(',', ''))
                total_funding += amount
                funding_count += 1
            except (ValueError, AttributeError):
                pass
        institution['total_funding'] = total_funding
        institution['funding_projects'] = funding_count
        institution['avg_funding'] = total_funding / funding_count if funding_count > 0 else 0
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        institutions_data = [inst for inst in institutions_data if search_query.lower() in inst['research_institution'].lower()]
    
    # Pagination
    paginator = Paginator(institutions_data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Research Institutions',
        'page_description': f'Browse {len(institutions_data)} research institutions funded by CIHR',
        'page_icon': 'fas fa-university',
        'show_breadcrumb': True,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_institutions': len(institutions_data),
    }
    return render(request, 'tracker/institutions.html', context)


def cihr_institutes(request):
    """CIHR institutes page showing all CIHR institutes with project counts"""
    # Get all CIHR institutes with project counts
    cihr_institutes_data = CIHRProject.objects.exclude(
        primary_institute__isnull=True
    ).exclude(
        primary_institute=''
    ).exclude(
        primary_institute__iexact='N/A'
    ).values('primary_institute').annotate(
        project_count=Count('primary_institute')
    ).order_by('-project_count')
    
    # Calculate total funding by CIHR institute
    for institute in cihr_institutes_data:
        total_funding = 0
        funding_count = 0
        for project in CIHRProject.objects.filter(primary_institute=institute['primary_institute']).exclude(cihr_amounts__isnull=True).exclude(cihr_amounts=''):
            try:
                amount = float(project.cihr_amounts.replace('$', '').replace(',', ''))
                total_funding += amount
                funding_count += 1
            except (ValueError, AttributeError):
                pass
        institute['total_funding'] = total_funding
        institute['funding_projects'] = funding_count
        institute['avg_funding'] = total_funding / funding_count if funding_count > 0 else 0
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        cihr_institutes_data = [inst for inst in cihr_institutes_data if search_query.lower() in inst['primary_institute'].lower()]
    
    # Pagination
    paginator = Paginator(cihr_institutes_data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'CIHR Institutes',
        'page_description': f'Browse {len(cihr_institutes_data)} CIHR institutes and their funded projects',
        'page_icon': 'fas fa-building',
        'show_breadcrumb': True,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_institutes': len(cihr_institutes_data),
    }
    return render(request, 'tracker/cihr_institutes.html', context)


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
