from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Value, Case, When, FloatField
from django.db.models.functions import Substr
from django.db import models
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import json
import re

from .models import CIHRProject
from .serializers import CIHRProjectSerializer, CIHRProjectListSerializer


def parse_funding_amount_python(amount_str):
    """Parse funding amount in Python - handles complex cases like semicolon-separated values"""
    if not amount_str or amount_str.upper() in ['N/A', 'NULL', '']:
        return None
    
    try:
        # Clean the string
        cleaned = str(amount_str).replace('$', '').replace(',', '').replace('"', '').strip()
        
        # Handle semicolon-separated values by taking the first one
        if ';' in cleaned:
            cleaned = cleaned.split(';')[0].strip()
        
        # Convert to float
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def safe_funding_annotation():
    """Simple safe annotation for funding amounts - avoids complex parsing"""
    # Just return a placeholder that we'll calculate in Python later
    return Value(0, output_field=FloatField())


def get_funding_stats_optimized():
    """Get funding statistics using optimized hybrid approach"""
    cache_key = 'funding_stats_v3'
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Get all projects with funding amounts
    all_projects = CIHRProject.objects.exclude(
        cihr_amounts__isnull=True
    ).exclude(
        cihr_amounts=''
    ).exclude(
        cihr_amounts__iexact='N/A'
    ).values(
        'cihr_amounts', 'therapeutic_area', 'primary_institute', 'primary_theme', 
        'broad_study_type', 'patient_engagement', 'indigenous_collaboration',
        'international_collaboration', 'health_equity', 'implementation_science', 
        'knowledge_translation_focus'
    )
    
    # Initialize results
    funding_stats = {
        'therapeutic_area': {},
        'primary_institute': {},
        'primary_theme': {},
        'broad_study_type': {}
    }
    
    focus_funding = {
        'patient_engagement': 0,
        'indigenous_collaboration': 0,
        'international_collaboration': 0,
        'health_equity': 0,
        'implementation_science': 0,
        'knowledge_translation': 0
    }
    
    total_funding = 0
    project_count = 0
    
    # Process all projects in Python for reliability
    for project in all_projects:
        amount = parse_funding_amount_python(project['cihr_amounts'])
        if amount and amount > 0:
            total_funding += amount
            project_count += 1
            
            # Group by categories
            for field in ['therapeutic_area', 'primary_institute', 'primary_theme', 'broad_study_type']:
                value = project.get(field)
                if value and value not in ['N/A', '', None]:
                    if value not in funding_stats[field]:
                        funding_stats[field][value] = 0
                    funding_stats[field][value] += amount
            
            # Process special focus areas
            if project.get('patient_engagement') == 'yes':
                focus_funding['patient_engagement'] += amount
            if project.get('indigenous_collaboration') == 'yes':
                focus_funding['indigenous_collaboration'] += amount
            if project.get('international_collaboration') == 'yes':
                focus_funding['international_collaboration'] += amount
            if project.get('health_equity') == 'yes':
                focus_funding['health_equity'] += amount
            if project.get('implementation_science') == 'yes':
                focus_funding['implementation_science'] += amount
            if project.get('knowledge_translation_focus') == 'yes':
                focus_funding['knowledge_translation'] += amount
    
    result = {
        'total_funding': total_funding,
        'project_count': project_count,
        'avg_funding': total_funding / project_count if project_count > 0 else 0,
        'by_category': funding_stats,
        'focus_areas': focus_funding
    }
    
    # Cache for 15 minutes
    cache.set(cache_key, result, 60 * 15)
    return result


@cache_page(60 * 5)  # Cache for 5 minutes
def home(request):
    """Home page with overview statistics - optimized with database aggregation"""
    
    # Get proper funding statistics using the working function
    funding_stats = get_funding_stats_optimized()
    
    # Get cached statistics or calculate them
    cache_key = 'home_stats'
    cached_stats = cache.get(cache_key)
    
    if not cached_stats:
        # Pre-calculate and cache expensive queries
        cached_stats = {
            'total_projects': CIHRProject.objects.count(),
            'therapeutic_areas': list(
                CIHRProject.objects.exclude(
                    therapeutic_area__isnull=True
                ).exclude(
                    therapeutic_area=''
                ).exclude(
                    therapeutic_area__iexact='N/A'
                ).values('therapeutic_area').annotate(
                    count=Count('therapeutic_area')
                ).order_by('-count')[:10]
            ),
            'primary_institutes': list(
                CIHRProject.objects.exclude(
                    primary_institute__isnull=True
                ).exclude(
                    primary_institute=''
                ).exclude(
                    primary_institute__iexact='N/A'
                ).values('primary_institute').annotate(
                    count=Count('primary_institute')
                ).order_by('-count')[:5]
            ),
        }
        cache.set(cache_key, cached_stats, 60 * 10)  # Cache for 10 minutes
    
    context = {
        'page_title': 'CIHR Projects Tracker',
        'page_description': 'Comprehensive database of Canadian Institutes of Health Research funded projects',
        'page_icon': 'fas fa-flag',
        'total_projects': cached_stats['total_projects'],
        'total_funding': funding_stats['total_funding'],
        'funding_projects': funding_stats['project_count'],
        'therapeutic_areas': cached_stats['therapeutic_areas'],
        'primary_institutes': cached_stats['primary_institutes'],
    }
    return render(request, 'tracker/home.html', context)


def project_list(request):
    """Project list with filtering and pagination - optimized"""
    # Base queryset with only necessary fields for list view
    projects = CIHRProject.objects.only(
        'project_id', 'project_title', 'principal_investigators',
        'research_institution', 'primary_institute', 'competition_year_month',
        'broad_study_type', 'therapeutic_area', 'cihr_amounts'
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(project_title__icontains=search_query) |
            Q(abstract_summary__icontains=search_query) |
            Q(keywords__icontains=search_query) |
            Q(principal_investigators__icontains=search_query)
        )
    
    # Filtering - optimized with exact lookups where possible
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
    
    # Get total count before pagination (optimized)
    total_results = projects.count()
    
    # Pagination
    paginator = Paginator(projects, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options - cached for performance
    cache_key = 'filter_options'
    filter_options = cache.get(cache_key)
    
    if not filter_options:
        # Use database aggregation for filter options
        filter_options = {
            'broad_study_types': list(
                CIHRProject.objects.values_list('broad_study_type', flat=True).distinct()
            ),
            'therapeutic_areas': list(
                CIHRProject.objects.exclude(
                    therapeutic_area__isnull=True
                ).exclude(
                    therapeutic_area=''
                ).exclude(
                    therapeutic_area__iexact='N/A'
                ).values_list('therapeutic_area', flat=True).distinct()[:20]
            ),
            'primary_institutes': list(
                CIHRProject.objects.exclude(
                    primary_institute__isnull=True
                ).exclude(
                    primary_institute=''
                ).exclude(
                    primary_institute__iexact='N/A'
                ).values_list('primary_institute', flat=True).distinct()
            ),
            'primary_themes': list(
                CIHRProject.objects.exclude(
                    primary_theme__isnull=True
                ).exclude(
                    primary_theme=''
                ).exclude(
                    primary_theme__iexact='N/A'
                ).values_list('primary_theme', flat=True).distinct()
            ),
            'competition_years': sorted(
                set([
                    year[:4] for year in CIHRProject.objects.exclude(
                        competition_year_month__isnull=True
                    ).values_list('competition_year_month', flat=True) if year
                ]), reverse=True
            ),
        }
        cache.set(cache_key, filter_options, 60 * 15)  # Cache for 15 minutes
    
    context = {
        'page_title': 'CIHR Projects',
        'page_description': f'Browse {total_results} CIHR-funded research projects',
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
        'total_results': total_results,
    }
    return render(request, 'tracker/project_list.html', context)


def project_detail(request, project_id):
    """Project detail page showing only 'yes' fields - optimized"""
    # Use select_related if there were foreign keys, but since there aren't, just get the object
    project = get_object_or_404(CIHRProject, project_id=project_id)
    
    # Get only fields with 'yes' values (cached per project)
    cache_key = f'project_yes_fields_{project_id}'
    yes_fields = cache.get(cache_key)
    
    if yes_fields is None:
        yes_fields = project.get_yes_fields()
        cache.set(cache_key, yes_fields, 60 * 30)  # Cache for 30 minutes
    
    context = {
        'page_title': f'Project {project.project_id}',
        'page_description': project.project_title,
        'page_icon': 'fas fa-file-alt',
        'show_breadcrumb': True,
        'project': project,
        'yes_fields': yes_fields,
    }
    return render(request, 'tracker/project_detail.html', context)


@cache_page(60 * 10)  # Cache for 10 minutes
def statistics(request):
    """Statistics and analytics page - completely optimized with database aggregation"""
    
    # Get cached statistics or calculate them
    cache_key = 'statistics_data'
    stats = cache.get(cache_key)
    
    if not stats:
        # All statistics calculated at database level
        total_projects = CIHRProject.objects.count()
        
        # Study type distribution
        study_types = list(
            CIHRProject.objects.values('broad_study_type').annotate(
                count=Count('broad_study_type')
            ).order_by('-count')
        )
        
        # Therapeutic area distribution  
        therapeutic_areas = list(
            CIHRProject.objects.exclude(
                therapeutic_area__isnull=True
            ).exclude(
                therapeutic_area=''
            ).exclude(
                therapeutic_area__iexact='N/A'
            ).values('therapeutic_area').annotate(
                count=Count('therapeutic_area')
            ).order_by('-count')[:15]
        )
        
        # Institute distribution
        institutes = list(
            CIHRProject.objects.exclude(
                primary_institute__isnull=True
            ).exclude(
                primary_institute=''
            ).exclude(
                primary_institute__iexact='N/A'
            ).values('primary_institute').annotate(
                count=Count('primary_institute')
            ).order_by('-count')[:10]
        )
        
        # Theme distribution
        themes = list(
            CIHRProject.objects.exclude(
                primary_theme__isnull=True
            ).exclude(
                primary_theme=''
            ).exclude(
                primary_theme__iexact='N/A'
            ).values('primary_theme').annotate(
                count=Count('primary_theme')
            ).order_by('-count')[:10]
        )
        
        # Year distribution - optimized with database functions
        year_distribution = dict(
            CIHRProject.objects.exclude(
                competition_year_month__isnull=True
            ).annotate(
                year=Substr('competition_year_month', 1, 4)
            ).values('year').annotate(
                count=Count('year')
            ).values_list('year', 'count')
        )
        
        # Technology adoption - batch query
        tech_stats = dict(
            CIHRProject.objects.aggregate(
                ai_machine_learning=Count(Case(When(ai_machine_learning='yes', then=1))),
                digital_health=Count(Case(When(digital_health='yes', then=1))),
                telemedicine=Count(Case(When(telemedicine='yes', then=1))),
                wearable_technology=Count(Case(When(wearable_technology='yes', then=1))),
                big_data_analytics=Count(Case(When(big_data_analytics='yes', then=1))),
                blockchain=Count(Case(When(blockchain='yes', then=1))),
            )
        )
        
        # Special focus areas - batch query
        focus_areas = dict(
            CIHRProject.objects.aggregate(
                patient_engagement=Count(Case(When(patient_engagement='yes', then=1))),
                indigenous_collaboration=Count(Case(When(indigenous_collaboration='yes', then=1))),
                international_collaboration=Count(Case(When(international_collaboration='yes', then=1))),
                health_equity=Count(Case(When(health_equity='yes', then=1))),
                implementation_science=Count(Case(When(implementation_science='yes', then=1))),
                knowledge_translation=Count(Case(When(knowledge_translation_focus='yes', then=1))),
            )
        )
        
        # FUNDING ANALYSIS - Use optimized hybrid approach
        funding_stats = get_funding_stats_optimized()
        
        # Extract totals
        funding_totals = {
            'total_funding': funding_stats['total_funding'],
            'funding_projects': funding_stats['project_count'],
            'avg_funding': funding_stats['avg_funding']
        }
        
        # Extract top funded therapeutic areas
        therapeutic_funding = funding_stats['by_category'].get('therapeutic_area', {})
        top_funded_areas = list(
            sorted(therapeutic_funding.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Extract funding by CIHR institute
        institute_funding = funding_stats['by_category'].get('primary_institute', {})
        top_funded_institutes = list(
            sorted(institute_funding.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Extract funding by study type
        study_type_funding = funding_stats['by_category'].get('broad_study_type', {})
        funding_by_study_type = dict(study_type_funding)
        
        # Extract funding by research theme
        theme_funding = funding_stats['by_category'].get('primary_theme', {})
        top_funded_themes = list(
            sorted(theme_funding.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Extract funding by special focus areas
        funding_by_focus = funding_stats['focus_areas']
        
        # Convert to more readable format
        funding_by_focus_readable = {
            'Patient Engagement': funding_by_focus['patient_engagement'],
            'Indigenous Collaboration': funding_by_focus['indigenous_collaboration'],
            'International Collaboration': funding_by_focus['international_collaboration'],
            'Health Equity': funding_by_focus['health_equity'],
            'Implementation Science': funding_by_focus['implementation_science'],
            'Knowledge Translation': funding_by_focus['knowledge_translation'],
        }
        
        stats = {
            'total_projects': total_projects,
            'study_types': study_types,
            'therapeutic_areas': therapeutic_areas,
            'institutes': institutes,
            'themes': themes,
            'year_distribution': dict(sorted(year_distribution.items())),
            'tech_stats': tech_stats,
            'focus_areas': focus_areas,
            'total_funding': funding_totals['total_funding'] or 0,
            'funding_projects': funding_totals['funding_projects'] or 0,
            'avg_funding': funding_totals['avg_funding'] or 0,
            'top_funded_areas': top_funded_areas,
            'top_funded_institutes': top_funded_institutes,
            'funding_by_study_type': funding_by_study_type,
            'top_funded_themes': top_funded_themes,
            'funding_by_focus': funding_by_focus_readable,
        }
        
        # Cache for 15 minutes
        cache.set(cache_key, stats, 60 * 15)
    
    context = {
        'page_title': 'Statistics & Analytics',
        'page_description': 'Comprehensive statistics and visualizations of CIHR projects',
        'page_icon': 'fas fa-chart-bar',
        'show_breadcrumb': True,
        **stats
    }
    return render(request, 'tracker/statistics.html', context)


def api_project_search(request):
    """AJAX endpoint for project search suggestions - optimized"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Use only() to fetch minimal fields for search
    projects = CIHRProject.objects.only(
        'project_id', 'project_title', 'principal_investigators'
    ).filter(
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


@cache_page(60 * 10)  # Cache for 10 minutes
def institutions(request):
    """Research institutions page - highly optimized"""
    
    cache_key = 'institutions_with_funding_v2'
    search_query = request.GET.get('search', '')
    
    # Include search in cache key
    if search_query:
        cache_key += f'_search_{hash(search_query)}'
    
    cached_result = cache.get(cache_key)
    if cached_result:
        institutions_with_funding, total_institutions = cached_result
    else:
        # Get all projects with funding data in one efficient query
        projects_query = CIHRProject.objects.exclude(
            research_institution__isnull=True
        ).exclude(
            research_institution=''
        ).exclude(
            research_institution__iexact='N/A'
        ).exclude(
            cihr_amounts__isnull=True
        ).exclude(
            cihr_amounts=''
        ).exclude(
            cihr_amounts__iexact='N/A'
        ).values('research_institution', 'cihr_amounts')
        
        # Apply search filter if provided
        if search_query:
            projects_query = projects_query.filter(
                research_institution__icontains=search_query
            )
        
        # Process all data in Python efficiently
        institution_stats = {}
        
        for project in projects_query:
            institution = project['research_institution']
            amount = parse_funding_amount_python(project['cihr_amounts'])
            
            if institution not in institution_stats:
                institution_stats[institution] = {
                    'research_institution': institution,
                    'project_count': 0,
                    'total_funding': 0,
                    'funding_projects': 0,
                    'avg_funding': 0
                }
            
            institution_stats[institution]['project_count'] += 1
            
            if amount and amount > 0:
                institution_stats[institution]['total_funding'] += amount
                institution_stats[institution]['funding_projects'] += 1
        
        # Calculate averages and sort
        institutions_with_funding = []
        for stats in institution_stats.values():
            if stats['funding_projects'] > 0:
                stats['avg_funding'] = stats['total_funding'] / stats['funding_projects']
            institutions_with_funding.append(stats)
        
        # Sort by project count
        institutions_with_funding.sort(key=lambda x: x['project_count'], reverse=True)
        total_institutions = len(institutions_with_funding)
        
        # Cache for 15 minutes
        cache.set(cache_key, (institutions_with_funding, total_institutions), 60 * 15)
    
    # Pagination
    paginator = Paginator(institutions_with_funding, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Research Institutions',
        'page_description': f'Browse {total_institutions} research institutions funded by CIHR',
        'page_icon': 'fas fa-university',
        'show_breadcrumb': True,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_institutions': total_institutions,
    }
    return render(request, 'tracker/institutions.html', context)


@cache_page(60 * 10)  # Cache for 10 minutes
def cihr_institutes(request):
    """CIHR institutes page - highly optimized"""
    
    cache_key = 'cihr_institutes_with_funding_v2'
    search_query = request.GET.get('search', '')
    
    # Include search in cache key
    if search_query:
        cache_key += f'_search_{hash(search_query)}'
    
    cached_result = cache.get(cache_key)
    if cached_result:
        institutes_with_funding, total_institutes = cached_result
    else:
        # Get all projects with funding data in one efficient query
        projects_query = CIHRProject.objects.exclude(
            primary_institute__isnull=True
        ).exclude(
            primary_institute=''
        ).exclude(
            primary_institute__iexact='N/A'
        ).exclude(
            cihr_amounts__isnull=True
        ).exclude(
            cihr_amounts=''
        ).exclude(
            cihr_amounts__iexact='N/A'
        ).values('primary_institute', 'cihr_amounts')
        
        # Apply search filter if provided
        if search_query:
            projects_query = projects_query.filter(
                primary_institute__icontains=search_query
            )
        
        # Process all data in Python efficiently
        institute_stats = {}
        
        for project in projects_query:
            institute = project['primary_institute']
            amount = parse_funding_amount_python(project['cihr_amounts'])
            
            if institute not in institute_stats:
                institute_stats[institute] = {
                    'primary_institute': institute,
                    'project_count': 0,
                    'total_funding': 0,
                    'funding_projects': 0,
                    'avg_funding': 0
                }
            
            institute_stats[institute]['project_count'] += 1
            
            if amount and amount > 0:
                institute_stats[institute]['total_funding'] += amount
                institute_stats[institute]['funding_projects'] += 1
        
        # Calculate averages and sort
        institutes_with_funding = []
        for stats in institute_stats.values():
            if stats['funding_projects'] > 0:
                stats['avg_funding'] = stats['total_funding'] / stats['funding_projects']
            institutes_with_funding.append(stats)
        
        # Sort by project count
        institutes_with_funding.sort(key=lambda x: x['project_count'], reverse=True)
        total_institutes = len(institutes_with_funding)
        
        # Cache for 15 minutes
        cache.set(cache_key, (institutes_with_funding, total_institutes), 60 * 15)
    
    # Pagination
    paginator = Paginator(institutes_with_funding, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'CIHR Institutes',
        'page_description': f'Browse {total_institutes} CIHR institutes',
        'page_icon': 'fas fa-building',
        'show_breadcrumb': True,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_institutes': total_institutes,
    }
    return render(request, 'tracker/cihr_institutes.html', context)


# API ViewSets (keep existing REST framework views but optimize)
class CIHRProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for CIHR projects - optimized"""
    queryset = CIHRProject.objects.all()
    serializer_class = CIHRProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['broad_study_type', 'therapeutic_area', 'primary_institute']
    search_fields = ['project_title', 'abstract_summary', 'keywords', 'principal_investigators']
    ordering_fields = ['project_id', 'competition_year_month']
    ordering = ['-project_id']
    
    def get_serializer_class(self):
        """Use list serializer for list view to reduce data transfer"""
        if self.action == 'list':
            return CIHRProjectListSerializer
        return CIHRProjectSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """API endpoint for statistics"""
        cache_key = 'api_statistics'
        stats = cache.get(cache_key)
        
        if not stats:
            stats = {
                'total_projects': CIHRProject.objects.count(),
                'study_types': list(
                    CIHRProject.objects.values('broad_study_type').annotate(
                        count=Count('broad_study_type')
                    ).order_by('-count')
                ),
                'therapeutic_areas': list(
                    CIHRProject.objects.exclude(
                        therapeutic_area__isnull=True
                    ).values('therapeutic_area').annotate(
                        count=Count('therapeutic_area')
                    ).order_by('-count')[:10]
                ),
            }
            cache.set(cache_key, stats, 60 * 15)
        
        return Response(stats)
