import logging
import configparser
import enum
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Time, Enum, Table, or_, and_, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime as dt


config = configparser.ConfigParser()
config.read('settings.ini')


eng_str = 'postgresql+psycopg2://{user}:{password}@{host}:5432/{db}'.format(
  user = config['BD']['User'],
  password = config['BD']['Password'],
  host = config['BD']['Host'],
  db = config['BD']['Base']
)

debug = False
if config['MAIN']['Debug'] == 'True':
    debug = True
else:
    debug = False

engine = create_engine(eng_str, echo=debug)
Base = declarative_base()

class Weekday(enum.Enum):
    Monday = 'Monday'
    Tuesday = 'Tuesday'
    Wednesday = 'Wednesday'
    Thursday = 'Thursday'
    Friday = 'Friday'
    Saturday = 'Saturday'
    Sunday = 'Sunday'

# intranet=> create type awayreason as enum ('sick', 'vacation', 'business_trip', 'm_leave');
class AwayReason(enum.Enum):
    sick = 'sick'
    vacation = 'vacation'
    business_trip = 'business trip'
    m_leave = 'maternity leave'


shiftstoschedules = Table('shiftstoschedules', Base.metadata,
                          Column('id', Integer, primary_key=True),
                          Column('shiftid', Integer, ForeignKey('shifts.id')),
                          Column('scheduleid', Integer, ForeignKey('schedules.id'))
                          )

class Shifts(Base):

    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    dow = Column(Enum(Weekday))
    tbegin = Column(Time)
    tend = Column(Time)
    schedules = relationship('Schedules', secondary=shiftstoschedules, backref='ref_shifts')

    def get_shifts_now(self, day_now, time_now):

        yesterday = {
            'Monday': 'Sunday',
            'Tuesday': 'Monday',
            'Wednesday': 'Tuesday',
            'Thursday': 'Wednesday',
            'Friday': 'Thursday',
            'Saturday': 'Friday',
            'Sunday': 'Saturday'
        }

        session = Session()

        qq = session.query(Shifts).filter(or_(
            and_(Shifts.tbegin < Shifts.tend, Shifts.tbegin < time_now, time_now < Shifts.tend, Shifts.dow == day_now),
            and_(Shifts.tend < Shifts.tbegin,
                 or_(
                     and_(Shifts.tbegin < time_now, time_now < '23:59:59.9999', Shifts.dow == day_now),
                     and_('00:00:00.001' < time_now, time_now < Shifts.tend, Shifts.dow == yesterday[day_now])
                 )
                 )
        ))

        res = []

        for sh in qq: res.append(sh.schedules[0].id)
        session.close()
        return res


class Schedules(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    shifts = relationship('Shifts', secondary=shiftstoschedules, backref='ref_schedules')

specstoengineers = Table('specstoengineers', Base.metadata,
                          Column('id', Integer, primary_key=True),
                          Column('specid', Integer, ForeignKey('specs.id')),
                          Column('engineerid', Integer, ForeignKey('engineers.id'))
                          )

class Engineers(Base):
    __tablename__ = 'engineers'
    id = Column(Integer, primary_key=True)
    fname = Column(String)
    lname = Column(String)
    seatnum = Column(String)
    ipphone = Column(Integer)
    scheduleid = Column(Integer, ForeignKey('schedules.id'))
    awayfrom = Column(DateTime)
    awaytill = Column(DateTime)
    awayreason = Column(Enum(AwayReason))
    specs = relationship('Specs', secondary=specstoengineers, backref='ref_engineers')

    def get_engineers_away_now(self):
        date_time_now = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
        session = Session()
        res=[]
        q = session.query(Engineers).filter(and_(Engineers.awayfrom < date_time_now, Engineers.awaytill > date_time_now))
        '''
        for eng in q:
            specs = []
            for spc in eng.specs:
                specs.append(spc.specname)
            res.append((eng.fname + " " + eng.lname, specs, eng.awayfrom, eng.awaytill))
        session.close()
        '''

        for eng in q: res.append(eng.id)
        return res

    def get_engineers_away_fut(self):
        date_time_now = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
        session = Session()
        res=[]
        q = session.query(Engineers).filter(Engineers.awayfrom > date_time_now)
        for eng in q:
            specs = []
            for spc in eng.specs:
                specs.append(spc.specname)
            res.append((eng.fname + " " + eng.lname, specs, eng.awayfrom, eng.awaytill))
        session.close()
        return res

    def get_engineer_now(self):
        time_now = dt.datetime.now().strftime('%H:%M')
        day_now = dt.datetime.now().strftime('%A')
        date_time_now = dt.datetime.now().strftime('%Y-%m-%d %H:%M')

        # time_now = '13:00'
        # day_now = 'Tuesday'

        Sh = Shifts()
        schedsnow = Sh.get_shifts_now(day_now, time_now)
        awaynow = self.get_engineers_away_now()

        session = Session()
        res = []
        q = session.query(Engineers).filter(Engineers.scheduleid.in_(schedsnow)).filter(Engineers.id.notin_(awaynow))
        for eng in q:
            specs = []
            for spc in eng.specs:
                specs.append(spc.specname)
            res.append((eng.fname + " " + eng.lname, specs))
        session.close()
        return res

    def get_tl_now(self):
        time_now = dt.datetime.now().strftime('%H:%M')
        day_now = dt.datetime.now().strftime('%A')

        # time_now = '13:00'
        # day_now = 'Tuesday'

        Sh = Shifts()
        schedsnow = Sh.get_shifts_now(day_now, time_now)

        session = Session()
        res = []
        q = session.query(Engineers).filter(Engineers.scheduleid.in_(schedsnow)).join(Engineers.specs).filter(Specs.specname=='TL')
        for eng in q:
            specs = []
            for spc in eng.specs:
                specs.append(spc.specname)
            res.append((eng.fname + " " + eng.lname, eng.ipphone, specs))
        session.close()
        return res

    def get_sme_now(self):
        time_now = dt.datetime.now().strftime('%H:%M')
        day_now = dt.datetime.now().strftime('%A')

        # time_now = '13:00'
        # day_now = 'Tuesday'

        Sh = Shifts()
        schedsnow = Sh.get_shifts_now(day_now, time_now)

        session = Session()
        res = []
        q = session.query(Engineers).filter(Engineers.scheduleid.in_(schedsnow)).join(Engineers.specs).filter(Specs.specname=='SME')
        for eng in q:
            specs = []
            for spc in eng.specs:
                specs.append(spc.specname)
            res.append((eng.fname + " " + eng.lname, specs))
        session.close()
        return res



class Specs(Base):
    __tablename__ = 'specs'
    id = Column(Integer, primary_key=True)
    specname = Column(String)
    engineers = relationship('Engineers', secondary=specstoengineers, backref='ref_specs')


class TrustedChats(Base):
    __tablename__ = 'trustedchats'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)
    name = Column(String)
    role = Column(String(50))

    def check_chat_id(chat_id):
        return False


Base.metadata.create_all(engine)
Session = sessionmaker() #<--- required once
Session.configure(bind=engine)
