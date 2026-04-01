"""
AU E-Voting System — Root URL Configuration
Serves API routes + frontend HTML pages.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import FileResponse, Http404
import os

def serve_frontend(request, filepath=''):
    """Serve static frontend HTML/assets from the parent directory."""
    frontend_dir = settings.FRONTEND_DIR

    # Default to index.html
    if not filepath:
        filepath = 'index.html'

    full_path = os.path.join(frontend_dir, filepath)

    # Security: prevent directory traversal
    full_path = os.path.realpath(full_path)
    if not full_path.startswith(os.path.realpath(str(frontend_dir))):
        raise Http404

    if os.path.isfile(full_path):
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.json': 'application/json',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
        }
        ext = os.path.splitext(full_path)[1].lower()
        content_type = content_types.get(ext, 'application/octet-stream')
        return FileResponse(open(full_path, 'rb'), content_type=content_type)

    raise Http404

urlpatterns = [
    # Django admin
    path('django-admin/', admin.site.urls),

    # API routes
    path('api/auth/', include('accounts.urls')),
    path('api/', include('elections.urls')),

    # Frontend: serve assets and HTML pages
    re_path(r'^(?P<filepath>assets/.*)$', serve_frontend),
    re_path(r'^(?P<filepath>student/.+\.html)$', serve_frontend),
    re_path(r'^(?P<filepath>admin/.+\.html)$', serve_frontend),
    path('', serve_frontend, {'filepath': 'index.html'}),
]
