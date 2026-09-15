# OPS Admin Django Project
# 使用 PyMySQL 替代 mysqlclient（仅 MySQL 模式；USE_SQLITE=true 本地演示时无需该依赖）
import os

if os.environ.get('USE_SQLITE', 'False').lower() != 'true':
    import pymysql
    pymysql.install_as_MySQLdb()
