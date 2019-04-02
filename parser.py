import sys
import re
from time import strftime, strptime
import xlrd
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from main import engine, Engineers, Schedules, Shifts, Specs


Session = sessionmaker(bind=engine)
session = Session()


def get_name_from_name(name):
    return name.split(" ")


def get_shift_id(shift_name):
    scedules_name_to_name = {
        "Buki 1 (morning)": "Buki 1",
        "Buki2": "Buki 2",
        "Dobro (morning)": "Dobro",
        "Slovo (morning)": "Slovo",
        "Psi 1 (morning)": "Psi 1",
        "Vedi (morning)": "Vedi"
    }
    shift_id = None
    try:
        shift_id = scedules_id_to_name[shift_name]
    except KeyError:
        shift_id = scedules_id_to_name[scedules_name_to_name[shift_name]]
    return shift_id


book = xlrd.open_workbook(sys.argv[1])
sh = book.sheet_by_index(1)

day_of_week = {
    10: 'Monday',
    11: 'Tuesday',
    12: 'Wednesday',
    13: 'Thursday',
    14: 'Friday',
    15: 'Saturday',
    16: 'Sunday'
}

session.execute('''TRUNCATE shiftstoschedules CASCADE''')
session.execute('''TRUNCATE shifts CASCADE''')
session.execute('''TRUNCATE schedules CASCADE''')
session.execute('''TRUNCATE engineers CASCADE''')
session.execute('''TRUNCATE specs CASCADE''')
session.commit()


specs = []
specs_name_to_id = {}
for idx, r in enumerate(sh.get_rows()):
    if idx > 0:
        if not r[2].value == "":
            s = re.sub(r'/()', '', r[2].value)
            s1 = s.split()
            for s2 in s1:
                if specs.count(s2) == 0:
                    specs.append(s2)


spec_id = 1
for s in specs:
    specs_name_to_id[s] = spec_id
    session.add(Specs(id=spec_id, specname=s))
    spec_id = spec_id + 1

session.commit()

id_shifts = 1
id_scedules = 1
scedules_id_to_name = {}

for idx, r in enumerate(sh.get_rows()):
    if idx > 11 and idx < 23:
        session.add(Schedules(id=id_scedules, name=r[8].value))
        session.commit()
        scedules_id_to_name[r[8].value] = id_scedules

        i = 0
        for i in range(7):
            dayOfWeek = 9 + i
            if r[dayOfWeek].value != "":
                session.add(Shifts(id=id_shifts,
                                   dow=day_of_week[dayOfWeek + 1],
                                   tbegin=r[dayOfWeek].value[:5],
                                   tend=r[dayOfWeek].value[6:12]))
                session.commit()
                query = "INSERT INTO shiftstoschedules (shiftid, \
                         scheduleid) VALUES ({}, {});".format(id_shifts,
                                                               id_scedules)
                session.execute(query)
                id_shifts = id_shifts + 1

        id_scedules = id_scedules + 1


eng_id = 1
for idx, r in enumerate(sh.get_rows()):
    if idx > 0:
        if not r[1].value == "":
            name = get_name_from_name(r[1].value)
            shift_id = get_shift_id(r[5].value)
            session.add(Engineers(id=eng_id,
                                  fname=name[1],
                                  lname=name[0],
                                  scheduleid=shift_id,
                                  ipphone=None,
                                  seatnum="Bez pik",
                                  awayfrom=None,
                                  awaytill=None,
                                  awayreason=None))
            session.commit()
            if not r[2].value == "":
                s = re.sub(r'/()', '', r[2].value)
                s1 = s.split()
                for s2 in s1:
                    query = "INSERT INTO specstoengineers (specid, engineerid) \
                             VALUES ({}, {});".format(
                                 specs_name_to_id.get(s2), eng_id)
                    session.execute(query)
            eng_id = eng_id + 1


session.commit()

session.execute('''UPDATE engineers SET ipphone = 77210 WHERE lname = \'Legkov\'''')
session.execute('''UPDATE engineers SET ipphone = 77213 WHERE lname = \'Friauf\'''')
session.execute('''UPDATE engineers SET ipphone = 77215 WHERE lname = \'Maslyannikov\'''')
session.execute('''UPDATE engineers SET ipphone = 77114 WHERE lname = \'Meshcheryakov\'''')
session.execute('''UPDATE engineers SET ipphone = 77215 WHERE lname = \'Chekaev\'''')
session.execute('''UPDATE engineers SET ipphone = 77221 WHERE lname = \'Gunkin\'''')

session.execute('''UPDATE engineers SET awayfrom = \'2019-01-01 12:00:00\', awaytill = \'2019-06-01 12:00:00\', awayreason = \'m_leave\' WHERE lname = \'Morkovina\'''')
session.commit()
