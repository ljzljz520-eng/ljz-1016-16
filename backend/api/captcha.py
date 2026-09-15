"""
Captcha - 登录验证码模块

策略说明：
- 验证码总开关（captcha_enabled）：关闭时任何情况都不要求验证码
- 默认不强制：同一用户名连续登录失败达到阈值（fail_threshold）后，才要求验证码
- 验证码为后端生成的 SVG 图片临时码：一次性、限时有效（5 分钟）
- 验证码错误与账号密码错误使用不同的错误码和提示语
"""
import base64
import random
import uuid
from datetime import timedelta

from django.utils import timezone

from .models import CaptchaRecord, LoginFailRecord, SystemConfig

# 配置键
KEY_CAPTCHA_ENABLED = 'captcha_enabled'
KEY_FAIL_THRESHOLD = 'captcha_fail_threshold'

# 默认值
DEFAULT_CAPTCHA_ENABLED = True   # 功能总开关默认开启（但默认不强制，见阈值逻辑）
DEFAULT_FAIL_THRESHOLD = 3       # 默认连续失败 3 次后要求验证码
MIN_THRESHOLD, MAX_THRESHOLD = 1, 10

CAPTCHA_TTL_SECONDS = 300        # 验证码有效期 5 分钟
CAPTCHA_LENGTH = 4

# 去除易混淆字符（0/O、1/I/L 等）
CAPTCHA_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
CAPTCHA_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#7b1fa2', '#f57c00', '#455a64']


# ==================== 配置读写 ====================

def _get_config_value(key, default):
    try:
        return SystemConfig.objects.get(key=key).value
    except SystemConfig.DoesNotExist:
        return str(default)


def _set_config_value(key, value, description=''):
    SystemConfig.objects.update_or_create(
        key=key,
        defaults={'value': str(value), 'description': description},
    )


def get_captcha_config():
    """获取验证码配置"""
    enabled = _get_config_value(
        KEY_CAPTCHA_ENABLED,
        'true' if DEFAULT_CAPTCHA_ENABLED else 'false',
    ).lower() == 'true'
    try:
        threshold = int(_get_config_value(KEY_FAIL_THRESHOLD, DEFAULT_FAIL_THRESHOLD))
    except (TypeError, ValueError):
        threshold = DEFAULT_FAIL_THRESHOLD
    threshold = max(MIN_THRESHOLD, min(MAX_THRESHOLD, threshold))
    return {
        'captcha_enabled': enabled,
        'fail_threshold': threshold,
    }


def update_captcha_config(enabled=None, threshold=None):
    """更新验证码配置（运维开关）"""
    if enabled is not None:
        _set_config_value(
            KEY_CAPTCHA_ENABLED,
            'true' if enabled else 'false',
            '登录验证码总开关：关闭后任何情况都不要求验证码',
        )
    if threshold is not None:
        threshold = max(MIN_THRESHOLD, min(MAX_THRESHOLD, int(threshold)))
        _set_config_value(
            KEY_FAIL_THRESHOLD,
            str(threshold),
            '同一账号连续登录失败达到该次数后强制验证码',
        )
    return get_captcha_config()


# ==================== 失败计数 ====================

def get_fail_count(username):
    if not username:
        return 0
    record = LoginFailRecord.objects.filter(username=username.strip().lower()).first()
    return record.fail_count if record else 0


def incr_fail_count(username):
    record, _ = LoginFailRecord.objects.get_or_create(
        username=username.strip().lower(),
        defaults={'fail_count': 0},
    )
    record.fail_count += 1
    record.save(update_fields=['fail_count', 'last_fail_at'])
    return record.fail_count


def reset_fail_count(username):
    LoginFailRecord.objects.filter(username=username.strip().lower()).delete()


def reset_all_fail_counts():
    LoginFailRecord.objects.all().delete()


def is_captcha_required(username):
    """判断该用户名当前是否需要验证码"""
    config = get_captcha_config()
    if not config['captcha_enabled']:
        return False
    return get_fail_count(username) >= config['fail_threshold']


# ==================== 验证码生成与校验 ====================

def generate_captcha():
    """生成验证码，返回 (captcha_id, svg_data_uri)"""
    code = ''.join(random.choices(CAPTCHA_CHARS, k=CAPTCHA_LENGTH))
    captcha_id = uuid.uuid4().hex
    CaptchaRecord.objects.create(
        captcha_id=captcha_id,
        code=code,
        expires_at=timezone.now() + timedelta(seconds=CAPTCHA_TTL_SECONDS),
    )
    # 惰性清理过期验证码
    CaptchaRecord.objects.filter(expires_at__lt=timezone.now()).delete()
    svg = _render_svg(code)
    data_uri = 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return captcha_id, data_uri


def verify_captcha(captcha_id, code):
    """
    校验验证码（一次性：取出后立即作废）。
    返回 (ok, error_code, message)
    """
    if not captcha_id or not code:
        return False, 'CAPTCHA_REQUIRED', '请先获取并填写验证码'

    record = CaptchaRecord.objects.filter(captcha_id=captcha_id).first()
    if record is None:
        return False, 'CAPTCHA_INVALID', '验证码错误或已过期'

    # 一次性：无论对错都作废
    was_used = record.is_used
    record.is_used = True
    record.save(update_fields=['is_used'])

    if was_used:
        return False, 'CAPTCHA_INVALID', '验证码错误或已过期'
    if record.expires_at < timezone.now():
        return False, 'CAPTCHA_INVALID', '验证码错误或已过期'
    if record.code.lower() != str(code).strip().lower():
        return False, 'CAPTCHA_INVALID', '验证码错误或已过期'
    return True, '', ''


# ==================== SVG 图片渲染 ====================

def _render_svg(code):
    """将验证码渲染为带干扰线/噪点的 SVG 图片"""
    width, height = 132, 44
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f8fa"/>',
    ]
    # 干扰线
    for _ in range(4):
        color = random.choice(CAPTCHA_COLORS)
        parts.append(
            f'<line x1="{random.uniform(0, width):.1f}" y1="{random.uniform(0, height):.1f}" '
            f'x2="{random.uniform(0, width):.1f}" y2="{random.uniform(0, height):.1f}" '
            f'stroke="{color}" stroke-width="1" opacity="0.4"/>'
        )
    # 噪点
    for _ in range(20):
        parts.append(
            f'<circle cx="{random.uniform(0, width):.1f}" cy="{random.uniform(0, height):.1f}" '
            f'r="1" fill="#999" opacity="0.5"/>'
        )
    # 字符（随机旋转/字号/颜色）
    for i, ch in enumerate(code):
        x = 18 + i * 28
        y = random.uniform(26, 34)
        rotate = random.uniform(-25, 25)
        size = random.randint(22, 28)
        color = random.choice(CAPTCHA_COLORS)
        parts.append(
            f'<text x="{x}" y="{y:.1f}" transform="rotate({rotate:.1f} {x} {y:.1f})" '
            f'font-family="monospace" font-size="{size}" font-weight="bold" '
            f'fill="{color}">{ch}</text>'
        )
    parts.append('</svg>')
    return ''.join(parts)
