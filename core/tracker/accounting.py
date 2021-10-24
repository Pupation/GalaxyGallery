from fastapi import BackgroundTasks, Header

from asyncio import sleep
from main import gg, config

async def accountingService(backgroundTasks):
    print("this is accounting service at background")
    await sleep(config.site.default.accounting_interval)
    backgroundTasks.add_task(accountingService, backgroundTasks)


@gg.get('/accountingService')
async def registerAccountingService(backgroundTasks: BackgroundTasks):
    backgroundTasks.add_task(accountingService, backgroundTasks)
    