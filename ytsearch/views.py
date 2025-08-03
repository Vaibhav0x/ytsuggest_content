from django.shortcuts import render

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import isodate  # Add this import

YOUTUBE_SEARCH_URL =os.getenv("YOUTUBE_SEARCH_URL")
YOUTUBE_VIDEO_URL = os.getenv("YOUTUBE_VIDEO_URL")

class YouTubeSearchAPIView(APIView):
    def get(self, request):
        query = request.GET.get("query")
        video_language = request.GET.get('videoLanguage', 'all')  # Add new parameter
        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Search for video IDs
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 50,
            "key": settings.YOUTUBE_API_KEY,
            "videoDuration": "medium",
            "videoDuration": "long",
        }

        # Add relevanceLanguage only if specific language is requested
        if video_language != 'all':
            search_params['relevanceLanguage'] = video_language

        search_res = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
        search_data = search_res.json()

        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        if not video_ids:
            return Response({"videos": []})

        # Step 2: Get video details
        video_params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": settings.YOUTUBE_API_KEY
        }
        video_res = requests.get(YOUTUBE_VIDEO_URL, params=video_params)
        
        video_data = video_res.json()

        def format_duration(duration_str):
            try:
                duration = isodate.parse_duration(duration_str)
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                if hours > 0:
                    return f"{hours}:{minutes:02d}:{seconds:02d}"
                return f"{minutes}:{seconds:02d}"
            except:
                return "00:00"

        # Step 3: Score videos (basic)
        def score_video(video):
            stats = video["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            return views + (likes * 2) + (comments * 3)

        videos = video_data.get("items", [])
        for v in videos:
            v["score"] = score_video(v)
            duration_str = v.get("contentDetails", {}).get("duration", "PT0S")
            v["duration"] = format_duration(duration_str)
            
            # Add language detection
            snippet = v.get("snippet", {})
            detected_language = (
                snippet.get("defaultAudioLanguage", 
                snippet.get("defaultLanguage", "unknown"))
            )
            
            # Add language info to response
            v["language"] = detected_language

        # Filter videos by language if specified
        if video_language != 'all':
            videos = [v for v in videos if v.get("language", "").startswith(video_language)]

        sorted_videos = sorted(videos, key=lambda x: x["score"], reverse=True)

        return Response({
            "topSuggestions": sorted_videos[:50],
            "allVideos": sorted_videos,
        })
