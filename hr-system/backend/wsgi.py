"""PythonAnywhere WSGI 入口"""
import sys
import os

# 项目路径
project_home = '/home/hqh888/jijuxie-hr/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app_pythonanywhere import app as application
