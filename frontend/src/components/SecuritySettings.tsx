'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader, Switch, Input, Button } from '@heroui/react';
import { ShieldCheck, Save, RotateCcw } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from '@/store/toast';

/**
 * 登录安全设置（验证码开关）
 * - 验证码总开关：关闭后任何情况都不要求验证码
 * - 失败阈值：同一账号连续登录失败达到该次数后强制验证码
 */
export function SecuritySettings() {
  const [enabled, setEnabled] = useState(true);
  const [threshold, setThreshold] = useState('3');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);

  const fetchConfig = async () => {
    try {
      const res = await api.getCaptchaConfig();
      if (res.success && res.data) {
        setEnabled(res.data.captcha_enabled);
        setThreshold(String(res.data.fail_threshold));
      } else {
        toast.error(res.message || '获取验证码配置失败');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    const value = parseInt(threshold, 10);
    if (isNaN(value) || value < 1 || value > 10) {
      toast.warning('失败阈值需为 1-10 的整数');
      return;
    }
    setSaving(true);
    try {
      const res = await api.updateCaptchaConfig({
        captcha_enabled: enabled,
        fail_threshold: value,
      });
      if (res.success && res.data) {
        setEnabled(res.data.captcha_enabled);
        setThreshold(String(res.data.fail_threshold));
        toast.success('验证码配置已保存');
      } else {
        toast.error(res.message || '保存失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleResetFails = async () => {
    setResetting(true);
    try {
      const res = await api.resetLoginFails();
      if (res.success) {
        toast.success('登录失败计数已清空');
      } else {
        toast.error(res.message || '操作失败');
      }
    } finally {
      setResetting(false);
    }
  };

  return (
    <Card className="border-none shadow-sm">
      <CardHeader className="px-6 pt-5 pb-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-800">登录安全设置</h3>
        </div>
      </CardHeader>
      <CardBody className="px-6 pb-5">
        {loading ? (
          <p className="text-sm text-gray-400">加载中...</p>
        ) : (
          <div className="flex flex-col gap-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">登录验证码</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  开启后，同一账号连续登录失败达到阈值时强制验证码校验；关闭则不启用
                </p>
              </div>
              <Switch
                isSelected={enabled}
                onValueChange={setEnabled}
                color="primary"
                aria-label="登录验证码开关"
              />
            </div>

            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">失败阈值</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  连续失败多少次后要求验证码（1-10 次）
                </p>
              </div>
              <Input
                type="number"
                min={1}
                max={10}
                value={threshold}
                onValueChange={setThreshold}
                isDisabled={!enabled}
                className="w-24"
                size="sm"
                variant="bordered"
                aria-label="失败阈值"
              />
            </div>

            <div className="flex items-center gap-3 pt-1">
              <Button
                color="primary"
                size="sm"
                startContent={<Save size={14} />}
                onPress={handleSave}
                isLoading={saving}
              >
                保存配置
              </Button>
              <Button
                variant="flat"
                size="sm"
                startContent={<RotateCcw size={14} />}
                onPress={handleResetFails}
                isLoading={resetting}
              >
                清空失败计数
              </Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
