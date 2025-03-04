import datetime
import asyncio


class PacketPoller:
    def __init__(self):
        pass

    async def start_polling(self):
        lasttime = datetime.datetime.strptime('05.06.2023 10:00', '%d.%m.%Y %H:%M')
        while True:
            try:
                if datetime.datetime.now().strftime('%H:%M') == '00:01':
                    await self.refresh_limits()

                if lasttime + datetime.timedelta(minutes=1) <= datetime.datetime.now():
                    await self.auto_posting()
                    lasttime = datetime.datetime.now()

                await asyncio.sleep(60)
            except Exception as e:
                print(e)

    async def refresh_limits(self):
        pass

    async def auto_posting(self):
        pass