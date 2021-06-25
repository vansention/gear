# Gear脚手架

## 入口

* main.py websocket和web server

* admin.py 管理系统

* schedule.py 定时任务

## 规约

### REST api

对于Model，例如 User. 框架自动生成 REST api， 格式为 /api/webquery/user/

### web service api

在 services/admin/ 中，创建 example.py。 编写函数 foo(name:str)。则可通过 /admin/service/example.foo/ 调用 。

在 liquid/service/中， 创建 example.py。 编写函数 foo(name:str)。 则可通过 /api/service/example.foo/ 调用。

web service api 有完善的权限设置功能以应对复杂的实际应用。

### websocket api

在 liquid/game/ 中，创建 example.py  创建异步 example.foo 提供 websocket api

## Model Cache

solid.app_model.cache_model 反射缓存行为，自动添加缓存

