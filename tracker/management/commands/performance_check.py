from django.core.management.base import BaseCommand
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone
from django.core.cache import cache
import time
import sys

from tracker.views import home, project_list, statistics
from tracker.models import CIHRProject


class Command(BaseCommand):
    help = 'Check application performance and database optimization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--views',
            action='store_true',
            help='Test view performance',
        )
        parser.add_argument(
            '--queries',
            action='store_true',
            help='Analyze database queries',
        )
        parser.add_argument(
            '--cache',
            action='store_true',
            help='Test cache performance',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all performance tests',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.test_views()
            self.test_queries()
            self.test_cache()
        else:
            if options['views']:
                self.test_views()
            if options['queries']:
                self.test_queries()
            if options['cache']:
                self.test_cache()

    def test_views(self):
        """Test view performance"""
        self.stdout.write(self.style.HTTP_INFO('\n=== VIEW PERFORMANCE TEST ==='))
        
        factory = RequestFactory()
        
        views_to_test = [
            ('Home', home, factory.get('/')),
            ('Project List', project_list, factory.get('/projects/')),
            ('Statistics', statistics, factory.get('/statistics/')),
        ]
        
        for view_name, view_func, request in views_to_test:
            # Clear cache for accurate testing
            cache.clear()
            
            # Reset query log
            connection.queries_log.clear()
            
            start_time = time.time()
            start_queries = len(connection.queries)
            
            try:
                response = view_func(request)
                end_time = time.time()
                end_queries = len(connection.queries)
                
                execution_time = (end_time - start_time) * 1000  # ms
                query_count = end_queries - start_queries
                
                if execution_time < 100:
                    time_style = self.style.SUCCESS
                elif execution_time < 500:
                    time_style = self.style.WARNING
                else:
                    time_style = self.style.ERROR
                
                if query_count < 5:
                    query_style = self.style.SUCCESS
                elif query_count < 10:
                    query_style = self.style.WARNING
                else:
                    query_style = self.style.ERROR
                
                self.stdout.write(
                    f'{view_name}: '
                    f'{time_style(f"{execution_time:.2f}ms")} | '
                    f'{query_style(f"{query_count} queries")}'
                )
                
                # Show slow queries
                slow_queries = [q for q in connection.queries if float(q['time']) > 0.1]
                if slow_queries:
                    self.stdout.write(f'  Slow queries for {view_name}:')
                    for query in slow_queries:
                        self.stdout.write(f'    {float(query["time"]):.3f}s: {query["sql"][:100]}...')
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'{view_name}: Error - {str(e)}')
                )

    def test_queries(self):
        """Analyze database queries"""
        self.stdout.write(self.style.HTTP_INFO('\n=== DATABASE QUERY ANALYSIS ==='))
        
        # Test basic queries
        queries_to_test = [
            ('Total projects count', lambda: CIHRProject.objects.count()),
            ('Project with funding', lambda: CIHRProject.objects.exclude(cihr_amounts__isnull=True).count()),
            ('Therapeutic areas', lambda: list(CIHRProject.objects.values('therapeutic_area').distinct()[:10])),
            ('Recent projects', lambda: list(CIHRProject.objects.order_by('-project_id')[:10])),
        ]
        
        for query_name, query_func in queries_to_test:
            connection.queries_log.clear()
            start_time = time.time()
            
            try:
                result = query_func()
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000
                query_count = len(connection.queries)
                
                self.stdout.write(
                    f'{query_name}: {execution_time:.2f}ms ({query_count} queries)'
                )
                
                if hasattr(result, '__len__'):
                    self.stdout.write(f'  Result count: {len(result)}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'{query_name}: Error - {str(e)}')
                )

    def test_cache(self):
        """Test cache performance"""
        self.stdout.write(self.style.HTTP_INFO('\n=== CACHE PERFORMANCE TEST ==='))
        
        # Test cache set/get performance
        test_data = {'test': 'data', 'timestamp': timezone.now().isoformat()}
        
        # Set performance
        start_time = time.time()
        cache.set('perf_test_key', test_data, 300)
        set_time = (time.time() - start_time) * 1000
        
        # Get performance
        start_time = time.time()
        cached_data = cache.get('perf_test_key')
        get_time = (time.time() - start_time) * 1000
        
        # Cleanup
        cache.delete('perf_test_key')
        
        self.stdout.write(f'Cache SET: {set_time:.2f}ms')
        self.stdout.write(f'Cache GET: {get_time:.2f}ms')
        
        if cached_data == test_data:
            self.stdout.write(self.style.SUCCESS('Cache integrity: OK'))
        else:
            self.stdout.write(self.style.ERROR('Cache integrity: FAILED'))
        
        # Test cache backend type
        from django.conf import settings
        cache_backend = settings.CACHES['default']['BACKEND']
        self.stdout.write(f'Cache backend: {cache_backend}')
        
        if 'redis' in cache_backend.lower():
            try:
                from django_redis import get_redis_connection
                redis_con = get_redis_connection("default")
                info = redis_con.info()
                self.stdout.write(f'Redis version: {info.get("redis_version", "Unknown")}')
                self.stdout.write(f'Redis memory usage: {info.get("used_memory_human", "Unknown")}')
                self.stdout.write(f'Redis connections: {info.get("connected_clients", "Unknown")}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Redis info error: {str(e)}'))

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}" 