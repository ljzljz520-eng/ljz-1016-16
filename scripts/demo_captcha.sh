#!/bin/bash
# 登录验证码流程演示脚本
# 用法: ./scripts/demo_captcha.sh [backend_url]
# 说明: 验证码明文从 SVG 源码解析，仅用于本地自动化演示
set -e
BASE=${1:-http://localhost:8000}/api

# 提取 JSON 字段
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print(eval(sys.argv[1]))" "$2" <<< "$1"; }

# 获取新验证码，输出 "captcha_id code"
new_captcha() {
  local resp cid code
  resp=$(curl -s "$BASE/auth/captcha/")
  cid=$(jget "$resp" "d['data']['captcha_id']")
  code=$(jget "$resp" "d['data']['image']" | sed 's/^data:image\/svg+xml;base64,//' | base64 -d | grep -o '>[A-Z0-9]<' | tr -d '><' | tr -d '\n')
  echo "$cid $code"
}

login() { # username password [captcha_id captcha_code]
  local body="{\"username\":\"$1\",\"password\":\"$2\""
  [ -n "$3" ] && body="$body,\"captcha_id\":\"$3\",\"captcha_code\":\"$4\""
  curl -s -X POST "$BASE/auth/login/" -H 'Content-Type: application/json' -d "$body}"
}

# 管理员登录（自动处理验证码），输出 token
admin_login() {
  local R
  R=$(login admin admin123)
  if [ "$(jget "$R" "d['success']")" != "True" ]; then
    read CID CODE <<< "$(new_captcha)"
    R=$(login admin admin123 "$CID" "$CODE")
  fi
  jget "$R" "d['data']['token']"
}

echo "========== 0. 重置演示环境（清空失败计数、恢复默认配置） =========="
TOKEN=$(admin_login)
curl -s -X POST "$BASE/auth/captcha/config/" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"captcha_enabled":true,"fail_threshold":3}' > /dev/null
curl -s -X POST "$BASE/auth/captcha/reset-fails/" -H "Authorization: Bearer $TOKEN" > /dev/null
echo "环境已重置: 开关=开, 阈值=3, 失败计数=0"

echo ""
echo "========== 1. 默认不强制验证码：失败达到阈值后才要求 =========="
for i in 1 2 3; do
  R=$(login admin wrong_pass)
  echo "第 $i 次失败 → $(jget "$R" "d['message']") | fail_count=$(jget "$R" "d['data'].get('fail_count')") | captcha_required=$(jget "$R" "d['data']['captcha_required']")"
done

echo ""
echo "========== 2. 达到阈值：正确密码但不填验证码 =========="
R=$(login admin admin123)
echo "→ error=$(jget "$R" "d['data']['error']") | $(jget "$R" "d['message']")"

echo ""
echo "========== 3. 验证码错误（与账号密码错误区分提示） =========="
read CID CODE <<< "$(new_captcha)"
R=$(login admin admin123 "$CID" "XXXX")
echo "→ error=$(jget "$R" "d['data']['error']") | $(jget "$R" "d['message']")"

echo ""
echo "========== 4. 正确验证码 + 正确密码 → 登录成功，计数清零 =========="
read CID CODE <<< "$(new_captcha)"
R=$(login admin admin123 "$CID" "$CODE")
echo "→ $(jget "$R" "d['message']") | token=$(jget "$R" "d['data']['token'][:30]")..."
R=$(curl -s "$BASE/auth/login-state/?username=admin")
echo "→ 登录后状态: fail_count=$(jget "$R" "d['data']['fail_count']") | captcha_required=$(jget "$R" "d['data']['captcha_required']")"

echo ""
echo "========== 5. 运维开关：关闭后任意失败次数都不要求验证码 =========="
TOKEN=$(admin_login)
curl -s -X POST "$BASE/auth/captcha/config/" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"captcha_enabled":false}' > /dev/null
echo "开关已关闭"
for i in 1 2 3 4; do
  R=$(login admin wrong_pass)
  echo "第 $i 次失败 → captcha_required=$(jget "$R" "d['data']['captcha_required']")"
done

echo ""
echo "========== 6. 恢复：重新打开开关并清空失败计数 =========="
curl -s -X POST "$BASE/auth/captcha/config/" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"captcha_enabled":true,"fail_threshold":3}' > /dev/null
curl -s -X POST "$BASE/auth/captcha/reset-fails/" -H "Authorization: Bearer $TOKEN" > /dev/null
R=$(curl -s "$BASE/auth/captcha/config/")
echo "已恢复: $(jget "$R" "d['data']")"
echo ""
echo "演示完成 ✔"
