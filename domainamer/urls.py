from django.urls import path

from .views import (
    reroll_recommendation_view,
    recommend_domains_view,
    watchlist_alerts_view,
    watchlist_check_view,
    watchlist_check_job_status_view,
    watchlist_view,
)

urlpatterns = [
    path("recommend/", recommend_domains_view, name="recommend-domains"),
    path("recommend/reroll/", reroll_recommendation_view, name="recommend-reroll"),
    path("watchlist/", watchlist_view, name="watchlist"),
    path("watchlist/check/", watchlist_check_view, name="watchlist-check"),
    path("watchlist/check-jobs/<int:job_id>/", watchlist_check_job_status_view, name="watchlist-check-job-status"),
    path("watchlist/alerts/", watchlist_alerts_view, name="watchlist-alerts"),
]
