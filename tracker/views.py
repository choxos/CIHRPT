from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Value, FloatField, Case, When
from django.db.models.functions import Cast, Replace, Substr
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


def parse_funding_amount_db():
    """Create a database expression to parse funding amounts"""
    return Cast(
        Replace(
            Replace(
                Replace('cihr_amounts', Value('$'), Value('')),
                Value(','), Value('')
            ),
            Value(' '), Value('')
        ),
        FloatField()
    )


@cache_page(60 * 5)  # Cache for 5 minutes
def home(request):
    """Home page with overview statistics - optimized with database aggregation"""
    
    # Use database aggregation for funding calculation
    funding_stats = CIHRProject.objects.exclude(
        cihr_amounts__isnull=True
    ).exclude(
        cihr_amounts=''
    ).exclude(
        cihr_amounts__iexact='N/A'
    ).annotate(
        funding_amount=parse_funding_amount_db()
    ).exclude(
        funding_amount__isnull=True
    ).exclude(
        funding_amount__lte=0
    ).aggregate(
        total_funding=Sum('funding_amount'),
        funding_projects=Count('id')
    )
    
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
        'total_funding': funding_stats['total_funding'] or 0,
        'funding_projects': funding_stats['funding_projects'] or 0,
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
        
        # FUNDING ANALYSIS - All at database level
        
        # Total funding calculation
        funding_totals = CIHRProject.objects.exclude(
            cihr_amounts__isnull=True
        ).exclude(
            cihr_amounts=''
        ).exclude(
            cihr_amounts__iexact='N/A'
        ).annotate(
            funding_amount=parse_funding_amount_db()
        ).exclude(
            funding_amount__isnull=True
        ).exclude(
            funding_amount__lte=0
        ).aggregate(
            total_funding=Sum('funding_amount'),
            funding_projects=Count('id'),
            avg_funding=Avg('funding_amount')
        )
        
        # Funding by therapeutic area
        top_funded_areas = list(
            CIHRProject.objects.exclude(
                therapeutic_area__isnull=True
            ).exclude(
                therapeutic_area=''
            ).exclude(
                therapeutic_area__iexact='N/A'
            ).exclude(
                cihr_amounts__isnull=True
            ).exclude(
                cihr_amounts=''
            ).annotate(
                funding_amount=parse_funding_amount_db()
            ).exclude(
                funding_amount__isnull=True
            ).exclude(
                funding_amount__lte=0
            ).values('therapeutic_area').annotate(
                total_funding=Sum('funding_amount'),
                project_count=Count('id')
            ).order_by('-total_funding')[:10].values_list('therapeutic_area', 'total_funding')
        )
        
        # Funding by CIHR institute
        top_funded_institutes = list(
            CIHRProject.objects.exclude(
                primary_institute__isnull=True
            ).exclude(
                primary_institute=''
            ).exclude(
                primary_institute__iexact='N/A'
            ).exclude(
                cihr_amounts__isnull=True
            ).exclude(
                cihr_amounts=''
            ).annotate(
                funding_amount=parse_funding_amount_db()
            ).exclude(
                funding_amount__isnull=True
            ).exclude(
                funding_amount__lte=0
            ).values('primary_institute').annotate(
                total_funding=Sum('funding_amount'),
                project_count=Count('id')
            ).order_by('-total_funding')[:10].values_list('primary_institute', 'total_funding')
        )
        
        # Funding by study type
        funding_by_study_type = dict(
            CIHRProject.objects.exclude(
                cihr_amounts__isnull=True
            ).exclude(
                cihr_amounts=''
            ).annotate(
                funding_amount=parse_funding_amount_db()
            ).exclude(
                funding_amount__isnull=True
            ).exclude(
                funding_amount__lte=0
            ).values('broad_study_type').annotate(
                total_funding=Sum('funding_amount')
            ).values_list('broad_study_type', 'total_funding')
        )
        
        # Funding by research theme
        top_funded_themes = list(
            CIHRProject.objects.exclude(
                primary_theme__isnull=True
            ).exclude(
                primary_theme=''
            ).exclude(
                primary_theme__iexact='N/A'
            ).exclude(
                cihr_amounts__isnull=True
            ).exclude(
                cihr_amounts=''
            ).annotate(
                funding_amount=parse_funding_amount_db()
            ).exclude(
                funding_amount__isnull=True
            ).exclude(
                funding_amount__lte=0
            ).values('primary_theme').annotate(
                total_funding=Sum('funding_amount')
            ).order_by('-total_funding')[:10].values_list('primary_theme', 'total_funding')
        )
        
        # Funding by special focus areas
        funding_by_focus = dict(
            CIHRProject.objects.exclude(
                cihr_amounts__isnull=True
            ).exclude(
                cihr_amounts=''
            ).annotate(
                funding_amount=parse_funding_amount_db()
            ).exclude(
                funding_amount__isnull=True
            ).exclude(
                funding_amount__lte=0
            ).aggregate(
                patient_engagement=Sum(Case(When(patient_engagement='yes', then='funding_amount'), default=0)),
                indigenous_collaboration=Sum(Case(When(indigenous_collaboration='yes', then='funding_amount'), default=0)),
                international_collaboration=Sum(Case(When(international_collaboration='yes', then='funding_amount'), default=0)),
                health_equity=Sum(Case(When(health_equity='yes', then='funding_amount'), default=0)),
                implementation_science=Sum(Case(When(implementation_science='yes', then='funding_amount'), default=0)),
                knowledge_translation=Sum(Case(When(knowledge_translation_focus='yes', then='funding_amount'), default=0)),
            )
        )
        
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
    """Research institutions page - completely optimized"""
    
    # Get institutions with aggregated data in a single query
    institutions_query = CIHRProject.objects.exclude(
        research_institution__isnull=True
    ).exclude(
        research_institution=''
    ).exclude(
        research_institution__iexact='N/A'
    ).annotate(
        funding_amount=parse_funding_amount_db()
    ).values('research_institution').annotate(
        project_count=Count('research_institution'),
        total_funding=Sum(
            Case(
                When(funding_amount__gt=0, then='funding_amount'),
                default=0,
                output_field=FloatField()
            )
        ),
        funding_projects=Count(
            Case(
                When(funding_amount__gt=0, then=1),
                output_field=FloatField()
            )
        ),
        avg_funding=Avg(
            Case(
                When(funding_amount__gt=0, then='funding_amount'),
                output_field=FloatField()
            )
        )
    ).order_by('-project_count')
    
    # Search functionality at database level
    search_query = request.GET.get('search', '')
    if search_query:
        institutions_query = institutions_query.filter(
            research_institution__icontains=search_query
        )
    
    # Get total count
    total_institutions = institutions_query.count()
    
    # Pagination
    paginator = Paginator(institutions_query, 25)
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
    """CIHR institutes page - completely optimized"""
    
    # Get CIHR institutes with aggregated data in a single query
    institutes_query = CIHRProject.objects.exclude(
        primary_institute__isnull=True
    ).exclude(
        primary_institute=''
    ).exclude(
        primary_institute__iexact='N/A'
    ).annotate(
        funding_amount=parse_funding_amount_db()
    ).values('primary_institute').annotate(
        project_count=Count('primary_institute'),
        total_funding=Sum(
            Case(
                When(funding_amount__gt=0, then='funding_amount'),
                default=0,
                output_field=FloatField()
            )
        ),
        funding_projects=Count(
            Case(
                When(funding_amount__gt=0, then=1),
                output_field=FloatField()
            )
        ),
        avg_funding=Avg(
            Case(
                When(funding_amount__gt=0, then='funding_amount'),
                output_field=FloatField()
            )
        )
    ).order_by('-project_count')
    
    # Search functionality at database level
    search_query = request.GET.get('search', '')
    if search_query:
        institutes_query = institutes_query.filter(
            primary_institute__icontains=search_query
        )
    
    # Get total count
    total_institutes = institutes_query.count()
    
    # Pagination
    paginator = Paginator(institutes_query, 25)
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
