from django.conf.urls import patterns, include, url
from DBoard.views import HelloTemplate

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'DjangoDBoard.views.home', name='home'),
    # url(r'^DjangoDBoard/', include('DjangoDBoard.DjangoDBoard.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^dashboard/', include('DBoard.urls')),
    # url(r'^blog/', include('blog.urls')),

    
)
