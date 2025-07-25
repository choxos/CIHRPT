from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = 'Clear all cached data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            help='Clear cache keys matching pattern (e.g., "stats*")',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all cache keys',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_cache_keys()
        elif options['pattern']:
            self.clear_pattern(options['pattern'])
        else:
            self.clear_all()

    def clear_all(self):
        """Clear all cache"""
        cache.clear()
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared all cache')
        )

    def clear_pattern(self, pattern):
        """Clear cache keys matching pattern"""
        try:
            from django_redis import get_redis_connection
            con = get_redis_connection("default")
            keys = con.keys(f"{settings.CACHES['default'].get('KEY_PREFIX', '')}*{pattern}*")
            if keys:
                con.delete(*keys)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleared {len(keys)} cache keys matching "{pattern}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'No cache keys found matching "{pattern}"')
                )
        except ImportError:
            self.stdout.write(
                self.style.WARNING('Pattern clearing only works with Redis cache backend')
            )

    def list_cache_keys(self):
        """List all cache keys"""
        try:
            from django_redis import get_redis_connection
            con = get_redis_connection("default")
            keys = con.keys(f"{settings.CACHES['default'].get('KEY_PREFIX', '')}*")
            if keys:
                self.stdout.write(f'Found {len(keys)} cache keys:')
                for key in sorted(keys):
                    self.stdout.write(f'  - {key.decode()}')
            else:
                self.stdout.write('No cache keys found')
        except ImportError:
            self.stdout.write(
                self.style.WARNING('Key listing only works with Redis cache backend')
            ) 