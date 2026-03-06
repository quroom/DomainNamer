from django.urls import path

from .views import recommend_domains_view

urlpatterns = [
    path("recommend/", recommend_domains_view, name="recommend-domains"),
]

