"""
API URL Configuration - API路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'servers', views.ServerViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'logs', views.OperationLogViewSet)

urlpatterns = [
    # 认证相关
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.user_info, name='user-info'),

    # 登录验证码
    path('auth/captcha/', views.captcha_image, name='captcha-image'),
    path('auth/captcha/config/', views.captcha_config, name='captcha-config'),
    path('auth/captcha/reset-fails/', views.captcha_reset_fails, name='captcha-reset-fails'),
    path('auth/login-state/', views.login_state, name='login-state'),

    # 仪表板
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),

    # REST API
    path('', include(router.urls)),
]
