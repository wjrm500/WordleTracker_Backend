import datetime
import hashlib
from typing import List
import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from database.models import Base
from database.models.Day import Day
from database.models.User import User

class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_engine(self.database_url, echo = False)
        Base.metadata.create_all(self.engine, checkfirst = True)
        self.session = scoped_session(sessionmaker(bind = self.engine))
        self.timezone = None
    
    def set_timezone(self, timezone) -> None:
        if timezone not in pytz.all_timezones:
            raise Exception('Invalid timezone')
        self.timezone = timezone
    
    def today(self) -> datetime.date:
        if self.timezone is None:
            raise Exception('No timezone has been set')
        return datetime.datetime.now(pytz.timezone(self.timezone)).date()
    
    def get_day_from_date(self, date: str) -> Day:
        return self.session.query(Day).filter_by(date = date).first()
    
    def login(self, username: str, password: str) -> None:
        user = self.session.query(User).filter_by(username = username).first()
        if user is not None:
            hash_to_match = user.password_hash
            if hashlib.md5(password.encode()).hexdigest() == hash_to_match:
                return
            raise Exception('Password incorrect')
        raise Exception('User does not exist')
    
    def truncate_day_table(self) -> None:
        self.session.execute('''DELETE FROM day''')
        self.session.commit()
    
    def delete_day(self, date: str) -> None:
        day = self.get_day_from_date(date)
        self.session.delete(day)
        self.session.commit()
        
    def get_data(self) -> List:
        today = self.today()
        all_days = []
        all_days_dict = {}
        for day in self.session.query(Day).all():
            all_days.append({
                "Date": day.date,
                "Kate": day.kate_score,
                "Will": day.will_score
            })
        if len(all_days) > 0:
            all_days = sorted(all_days, key = lambda x: x['Date'])
            all_days_dict = {str(x['Date']): x for x in all_days}
            earliest_date = all_days[0]['Date']
        else:
            earliest_date = today
        earliest_date_weekday = earliest_date.weekday()
        start_date = earliest_date - datetime.timedelta(days = earliest_date_weekday)
        all_weeks = []
        while start_date <= today:
            single_week = []
            for _ in range(7):
                future = start_date >= today
                default_score = None if future else 8
                str_start_date = str(start_date)
                if str_start_date in all_days_dict:
                    data = all_days_dict[str_start_date]
                    kate_score = data['Kate'] or default_score
                    will_score = data['Will'] or default_score
                else:
                    kate_score = will_score = default_score
                single_week.append({
                    'Date': str_start_date,
                    'Kate': kate_score,
                    'Will': will_score
                })
                start_date = start_date + datetime.timedelta(days = 1)
            all_weeks.append(single_week)
        return all_weeks
    
    def add_score(self, date: str, score: int, user: str) -> None:
        day = self.get_day_from_date(date)
        if day is not None:
            if user == 'wjrm500':
                day.will_score = score
            elif user == 'kjem500':
                day.kate_score = score
        else:
            input_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            opponent_score = None if input_date == self.today() else 8
            if user == 'wjrm500':
                day = Day(
                    date = input_date,
                    will_score = score,
                    kate_score = opponent_score
                )
            elif user == 'kjem500':
                day = Day(
                    date = input_date,
                    will_score = opponent_score,
                    kate_score = score
                )
            self.session.add(day)
        self.session.commit()