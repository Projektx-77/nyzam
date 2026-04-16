# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'students', StudentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'events', EventViewSet)
router.register(r'attendance', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', UserViewSet.as_view({'get': 'me'}), name='auth_me'),
    path('statistics/', StatisticsViewSet.as_view({'get': 'dashboard_stats'}), name='dashboard_stats'),
    path('statistics/summary-cards/', StatisticsViewSet.as_view({'get': 'summary_cards'}), name='summary_cards'),
    path('statistics/student/', StatisticsViewSet.as_view({'get': 'student_statistics'}), name='student_stats'),
    path('statistics/group/', StatisticsViewSet.as_view({'get': 'group_statistics'}), name='group_stats'),
]
