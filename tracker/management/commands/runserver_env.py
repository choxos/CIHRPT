from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Run development server using PORT and HOST from environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            help='Override the PORT from environment',
        )
        parser.add_argument(
            '--host',
            help='Override the HOST from environment',
        )
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Show current server configuration',
        )

    def handle(self, *args, **options):
        # Get configuration from settings (which reads from .env)
        port = options.get('port') or getattr(settings, 'PORT', 8000)
        host = options.get('host') or getattr(settings, 'HOST', '127.0.0.1')
        
        if options['show_config']:
            self.stdout.write(self.style.SUCCESS('🔧 Server Configuration:'))
            self.stdout.write(f'   Host: {host}')
            self.stdout.write(f'   Port: {port}')
            self.stdout.write(f'   Full URL: http://{host}:{port}/')
            self.stdout.write('')
            self.stdout.write('💡 Tips:')
            self.stdout.write('   - Change PORT in your .env file to use different port')
            self.stdout.write('   - Use --port 8001 to override for this session')
            self.stdout.write('   - Use python manage.py runserver_env to start server')
            return
        
        # Display startup info
        self.stdout.write(self.style.SUCCESS('🚀 Starting Django development server...'))
        self.stdout.write(f'   📍 Server will be available at: http://{host}:{port}/')
        self.stdout.write(f'   🔧 Using PORT={port} from environment')
        self.stdout.write('')
        
        # Run the standard runserver command with our config
        try:
            call_command('runserver', f'{host}:{port}')
        except KeyboardInterrupt:
            self.stdout.write('\n👋 Server stopped gracefully.')
            sys.exit(0) 