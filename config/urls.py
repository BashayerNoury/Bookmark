from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

FRONTEND_DIST = Path(settings.BASE_DIR) / 'frontend' / 'dist'


def spa_index(_request):
    index = FRONTEND_DIST / 'index.html'
    if not index.exists():
        raise Http404('Frontend build missing. Run: cd frontend && npm run build')
    return FileResponse(index.open('rb'), content_type='text/html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', include('accounts.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/', include('accounts.urls_profile')),
    path('api/', include('books.urls')),
]

if FRONTEND_DIST.exists():
    urlpatterns += [
        path('assets/<path:path>', serve, {'document_root': FRONTEND_DIST / 'assets'}),
        path('favicon.svg', serve, {'document_root': FRONTEND_DIST, 'path': 'favicon.svg'}),
        re_path(r'^(?!api/|admin/|static/).*$', spa_index),
    ]
