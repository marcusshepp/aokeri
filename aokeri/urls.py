from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^foo/', admin.site.urls),
    url(r'^', include('main.urls')),
]
