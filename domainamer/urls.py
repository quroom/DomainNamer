from django.urls import path

from .views import (
    home_view,
    playground_view,
    reroll_recommendation_view,
    recommend_domains_view,
    service_recommendation_view,
    watchlist_alerts_view,
    watchlist_check_view,
    watchlist_check_job_status_view,
    watchlist_view,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("playground/", playground_view, name="playground"),
    path("recommend/", recommend_domains_view, name="recommend-domains"),
    path("recommend/service/", service_recommendation_view, name="recommend-service"),
    path("recommend/reroll/", reroll_recommendation_view, name="recommend-reroll"),
    path("watchlist/", watchlist_view, name="watchlist"),
    path("watchlist/check/", watchlist_check_view, name="watchlist-check"),
    path("watchlist/check-jobs/<int:job_id>/", watchlist_check_job_status_view, name="watchlist-check-job-status"),
    path("watchlist/alerts/", watchlist_alerts_view, name="watchlist-alerts"),
]
