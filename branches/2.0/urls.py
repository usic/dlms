from django.conf.urls.defaults import *



# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    (r'^dlms/$', 'dlms.views.index'),
    (r'^dlms/login/$', 'dlms.views.doLogin'),
    #(r'^dlms/add/$', 'dlms.views.addItem'),
    (r'^dlms/delete/(?P<hash_string>\w+)/', 'dlms.views.delItem'),

    # Example:
    # (r'^usic/', include('usic.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
