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

    url(r'^$', 'DBoard.views.index'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^hello/$', 'DBoard.views.hello'),
    url(r'^hello_template/$', 'DBoard.views.hello_template'),
    url(r'^hello_template_simple/$', 'DBoard.views.hello_template_simple'),
    url(r'^hello_class_view/$', HelloTemplate.as_view()),
    url(r'^status_check/$', 'DBoard.views.status_check'),
    url(r'^monthly_summary/$', 'DBoard.views.monthly_summary'),
    url(r'^index/$', 'DBoard.views.index'),
    url(r'^individual_index/$', 'DBoard.views.individual_index'),
    url(r'^individual_site/(?P<jobid>.+)$', 'DBoard.views.individual_site'),


    
)
