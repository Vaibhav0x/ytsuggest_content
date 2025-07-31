from django.urls import path
from .views import YouTubeSearchAPIView

urlpatterns = [
    path("search/", YouTubeSearchAPIView.as_view(), name="youtube_search"),
]
