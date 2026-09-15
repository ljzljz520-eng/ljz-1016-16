"""
API Views - 视图层
"""
import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Avg
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Server, Alert, Task, OperationLog
from .serializers import (
    UserSerializer, LoginSerializer, ServerSerializer,
    AlertSerializer, TaskSerializer, OperationLogSerializer,
    DashboardStatsSerializer
)
from .authentication import generate_token
from . import captcha as captcha_svc

logger = logging.getLogger(__name__)


def api_response(success: bool, data=None, message: str = '', code: int = 200):
    """统一API响应格式"""
    return Response({
        'success': success,
        'code': code,
        'message': message,
        'data': data,
    }, status=code if code < 400 else code)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    用户登录（含验证码策略）

    - 默认不强制验证码；同一用户名连续失败达到阈值后强制验证码
    - 验证码错误（CAPTCHA_REQUIRED/CAPTCHA_INVALID）与账号密码错误（BAD_CREDENTIALS）
      使用不同的 error 码和提示语，前端据此区分展示
    """
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(False, message='请输入用户名和密码', code=400)

    username = serializer.validated_data['username'].strip()
    password = serializer.validated_data['password']
    captcha_id = request.data.get('captcha_id', '')
    captcha_code = request.data.get('captcha_code', '')

    # 1) 需要验证码时，先校验验证码（与账号密码校验严格分开）
    if captcha_svc.is_captcha_required(username):
        ok, error_code, error_msg = captcha_svc.verify_captcha(captcha_id, captcha_code)
        if not ok:
            logger.info(f"用户 {username} 登录验证码校验失败: {error_code}")
            return api_response(False, data={
                'error': error_code,
                'captcha_required': True,
            }, message=error_msg, code=400)

    # 2) 校验账号密码
    user = authenticate(username=username, password=password)

    if user is None:
        fail_count = captcha_svc.incr_fail_count(username)
        config = captcha_svc.get_captcha_config()
        captcha_required = config['captcha_enabled'] and fail_count >= config['fail_threshold']
        logger.info(f"用户 {username} 登录失败（第 {fail_count} 次），需要验证码: {captcha_required}")
        return api_response(False, data={
            'error': 'BAD_CREDENTIALS',
            'fail_count': fail_count,
            'fail_threshold': config['fail_threshold'],
            'captcha_required': captcha_required,
        }, message='用户名或密码错误', code=401)

    if not user.is_active:
        return api_response(False, message='用户已被禁用', code=403)

    # 3) 登录成功：清零该用户的失败计数
    captcha_svc.reset_fail_count(username)

    token = generate_token(user)

    # 记录登录日志
    OperationLog.objects.create(
        action='用户登录',
        description=f'用户 {username} 登录系统',
        user=user,
        ip_address=get_client_ip(request)
    )

    logger.info(f"用户 {username} 登录成功")

    return api_response(True, data={
        'token': token,
        'user': UserSerializer(user).data
    }, message='登录成功')


@api_view(['GET'])
@permission_classes([AllowAny])
def captcha_image(request):
    """获取验证码图片（SVG data URI，一次性、5 分钟有效）"""
    captcha_id, image = captcha_svc.generate_captcha()
    return api_response(True, data={
        'captcha_id': captcha_id,
        'image': image,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def login_state(request):
    """查询指定用户名的登录状态（是否需要验证码），供登录页动态展示"""
    username = request.query_params.get('username', '').strip()
    config = captcha_svc.get_captcha_config()
    fail_count = captcha_svc.get_fail_count(username)
    return api_response(True, data={
        'captcha_enabled': config['captcha_enabled'],
        'fail_threshold': config['fail_threshold'],
        'fail_count': fail_count,
        'captcha_required': config['captcha_enabled'] and fail_count >= config['fail_threshold'],
    })


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def captcha_config(request):
    """
    验证码开关配置
    - GET：任何人可查看（登录页需要据此展示）
    - POST：修改配置，需管理员登录
    """
    if request.method == 'GET':
        return api_response(True, data=captcha_svc.get_captcha_config())

    # POST 需要管理员权限
    if not (request.user and request.user.is_authenticated and request.user.is_staff):
        return api_response(False, message='需要管理员权限才能修改验证码配置', code=403)

    enabled = request.data.get('captcha_enabled')
    threshold = request.data.get('fail_threshold')

    if enabled is not None and not isinstance(enabled, bool):
        return api_response(False, message='captcha_enabled 必须为布尔值', code=400)
    if threshold is not None:
        try:
            threshold = int(threshold)
        except (TypeError, ValueError):
            return api_response(False, message='fail_threshold 必须为整数', code=400)

    config = captcha_svc.update_captcha_config(enabled=enabled, threshold=threshold)

    OperationLog.objects.create(
        action='修改验证码配置',
        description=f"验证码开关: {'开' if config['captcha_enabled'] else '关'}，失败阈值: {config['fail_threshold']}",
        user=request.user,
        ip_address=get_client_ip(request)
    )
    logger.info(f"管理员 {request.user.username} 修改验证码配置: {config}")

    return api_response(True, data=config, message='验证码配置已保存')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def captcha_reset_fails(request):
    """清空所有登录失败计数（管理员，用于运维处理/演示）"""
    if not request.user.is_staff:
        return api_response(False, message='需要管理员权限', code=403)
    captcha_svc.reset_all_fail_counts()
    OperationLog.objects.create(
        action='清空登录失败计数',
        description='管理员清空所有登录失败计数',
        user=request.user,
        ip_address=get_client_ip(request)
    )
    return api_response(True, message='登录失败计数已清空')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """获取当前用户信息"""
    return api_response(True, data=UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    # 记录登出日志
    OperationLog.objects.create(
        action='用户登出',
        description=f'用户 {request.user.username} 退出系统',
        user=request.user,
        ip_address=get_client_ip(request)
    )
    return api_response(True, message='登出成功')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """获取仪表板统计数据"""
    # 服务器统计
    total_servers = Server.objects.count()
    running_servers = Server.objects.filter(status='running').count()
    stopped_servers = Server.objects.filter(status='stopped').count()
    warning_servers = Server.objects.filter(status='warning').count()
    
    # 告警统计
    total_alerts = Alert.objects.count()
    pending_alerts = Alert.objects.filter(status='pending').count()
    danger_alerts = Alert.objects.filter(level='danger', status='pending').count()
    
    # 任务统计
    total_tasks = Task.objects.count()
    pending_tasks = Task.objects.filter(status='pending').count()
    in_progress_tasks = Task.objects.filter(status='in_progress').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    # 资源使用率统计
    running_server_stats = Server.objects.filter(status='running').aggregate(
        avg_cpu=Avg('cpu_usage'),
        avg_memory=Avg('memory_usage'),
        avg_disk=Avg('disk_usage')
    )
    
    stats = {
        'total_servers': total_servers,
        'running_servers': running_servers,
        'stopped_servers': stopped_servers,
        'warning_servers': warning_servers,
        'total_alerts': total_alerts,
        'pending_alerts': pending_alerts,
        'danger_alerts': danger_alerts,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'avg_cpu_usage': round(running_server_stats['avg_cpu'] or 0, 2),
        'avg_memory_usage': round(running_server_stats['avg_memory'] or 0, 2),
        'avg_disk_usage': round(running_server_stats['avg_disk'] or 0, 2),
    }
    
    return api_response(True, data=stats)


class ServerViewSet(viewsets.ModelViewSet):
    """服务器视图集"""
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, data=serializer.data)
    
    def retrieve(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, data=serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    """告警视图集"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        level_filter = request.query_params.get('level')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if level_filter:
            queryset = queryset.filter(level=level_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, data=serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        priority_filter = request.query_params.get('priority')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, data=serializer.data)


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志视图集"""
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.get_queryset()[:50]  # 最近50条
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, data=serializer.data)


def get_client_ip(request):
    """获取客户端IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
