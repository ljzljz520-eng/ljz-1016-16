"""
OPS Admin Models - 运维后台数据模型
"""
from django.db import models
from django.contrib.auth.models import User


class Server(models.Model):
    """服务器模型"""
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('warning', '警告'),
        ('error', '错误'),
    ]
    
    name = models.CharField('服务器名称', max_length=100)
    ip_address = models.CharField('IP地址', max_length=45)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='running')
    cpu_usage = models.DecimalField('CPU使用率', max_digits=5, decimal_places=2, default=0)
    memory_usage = models.DecimalField('内存使用率', max_digits=5, decimal_places=2, default=0)
    disk_usage = models.DecimalField('磁盘使用率', max_digits=5, decimal_places=2, default=0)
    os_type = models.CharField('操作系统', max_length=50, default='Linux')
    location = models.CharField('所在位置', max_length=100, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ops_server'
        verbose_name = '服务器'
        verbose_name_plural = '服务器'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class Alert(models.Model):
    """告警模型"""
    LEVEL_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('danger', '危险'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
    ]
    
    title = models.CharField('告警标题', max_length=200)
    description = models.TextField('告警描述', blank=True)
    level = models.CharField('告警级别', max_length=20, choices=LEVEL_CHOICES, default='info')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    server = models.ForeignKey(
        Server, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='alerts',
        verbose_name='关联服务器'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    resolved_at = models.DateTimeField('解决时间', null=True, blank=True)

    class Meta:
        db_table = 'ops_alert'
        verbose_name = '告警'
        verbose_name_plural = '告警'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Task(models.Model):
    """任务模型"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    name = models.CharField('任务名称', max_length=200)
    description = models.TextField('任务描述', blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='负责人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'ops_task'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class SystemConfig(models.Model):
    """系统配置模型（键值对，用于验证码开关等运维配置）"""
    key = models.CharField('配置键', max_length=50, unique=True)
    value = models.CharField('配置值', max_length=200)
    description = models.CharField('说明', max_length=200, blank=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ops_config'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def __str__(self):
        return f"{self.key} = {self.value}"


class LoginFailRecord(models.Model):
    """登录失败记录（按用户名统计连续失败次数）"""
    username = models.CharField('用户名', max_length=150, unique=True)
    fail_count = models.IntegerField('连续失败次数', default=0)
    last_fail_at = models.DateTimeField('最后失败时间', auto_now=True)

    class Meta:
        db_table = 'ops_login_fail'
        verbose_name = '登录失败记录'
        verbose_name_plural = '登录失败记录'

    def __str__(self):
        return f"{self.username} 连续失败 {self.fail_count} 次"


class CaptchaRecord(models.Model):
    """验证码记录（后端生成的临时码，一次性、限时有效）"""
    captcha_id = models.CharField('验证码ID', max_length=64, unique=True)
    code = models.CharField('验证码', max_length=8)
    expires_at = models.DateTimeField('过期时间')
    is_used = models.BooleanField('是否已使用', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'ops_captcha'
        verbose_name = '验证码'
        verbose_name_plural = '验证码'
        ordering = ['-created_at']

    def __str__(self):
        return f"Captcha({self.captcha_id[:8]})"


class OperationLog(models.Model):
    """操作日志模型"""
    action = models.CharField('操作', max_length=100)
    description = models.TextField('描述', blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='操作人'
    )
    ip_address = models.CharField('IP地址', max_length=45, blank=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        db_table = 'ops_log'
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.created_at}"
