import logging

from datetime import datetime

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.jobstores.redis import RedisJobStore

from solid import init_log
from task.package import add
from task.redpack import unfreeze

init_log()

jobstores = {
    # 'default': RedisJobStore()
}

scheduler = BlockingScheduler(jobstores=jobstores)
scheduler.add_job(unfreeze, 'interval', minutes=1, id='unfreeze', replace_existing=True)
scheduler.start()
