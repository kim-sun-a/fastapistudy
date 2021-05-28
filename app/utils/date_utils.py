from datetime import datetime, date, timedelta


class D:
    def __init__(self, *args):
        self.utc_now = datetime.utcnow()
        self.timedelta = 0

    @classmethod
    def datetime(cls, diff: int=0) -> datetime:     # 데이터가 20210101 (int) 형식으로 들어오게
        return cls().utc_now + timedelta(hours=diff) if diff > 0 else cls().utc_now + timedelta(hours=diff)

    @classmethod
    def date(cls, diff: int=0) -> date:     # 데이터가 20210101 (int) 형식으로 들어오게
        return cls.datetime(diff=diff).date()

    @classmethod
    def date_num(cls, diff: int=0) -> int:   # 데이터가 20210101 (int) 형식으로 들어오게
        return int(cls.date(diff=diff).strftime('%Y%m%d'))