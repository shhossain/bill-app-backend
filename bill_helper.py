import imp
import sqlite3
from sys import platform
import requests
from bs4 import BeautifulSoup

colors = {'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m',
          'magenta': '\033[95m', 'cyan': '\033[96m', 'white': '\033[97m', 'end': '\033[0m'}


def custom_print(*args, color):
    print(colors[color], *args, colors['end'])


if platform == 'linux':
    USERDATA_PATH = "/home/sh0338/mysite/users.db"
    UNITDATA_PATH = "/home/sh0338/mysite/units.db"
    BILLDATA_PATH = "/home/sh0338/mysite/bills.db"
    WATERDATA_PATH = "/home/sh0338/mysite/water.db"
else:
    USERDATA_PATH = "users.db"
    UNITDATA_PATH = "units.db"
    BILLDATA_PATH = "bills.db"
    WATERDATA_PATH = "water.db"


class UserData:
    def __init__(self, db_name):
        if not (".db" in db_name or ".sqlite3" in db_name):
            db_name = db_name + '.db'
        self.db_name = db_name

        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.db.cursor()

        self.c.execute(
            "CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name STRING,password STRING,housename STRING,role STRING,email STRING UNIQUE)")

    def insert_user(self, name, password, housename, role, email):
        # check if name, housename and email are unique
        q = "SELECT * FROM users WHERE name = ? AND housename = ? AND email = ?"
        self.c.execute(q, (name, housename, email))
        if self.c.fetchone():
            return False
        # insert user
        q = "INSERT INTO users(name, password, housename, role, email) VALUES(?, ?, ?, ?, ?)"
        self.c.execute(q, (name, password, housename, role, email))
        self.db.commit()

    def delete_user(self, name, housename):
        # delete from userdata,unitdata,billdata
        q = "DELETE FROM users WHERE name = ? AND housename = ?"
        self.c.execute(q, (name, housename))
        self.db.commit()

        unitdata = UnitData(UNITDATA_PATH)
        unitdata.delete_all_units(name, housename)

        billdata = BillData(BILLDATA_PATH)
        billdata.delete_all_bills(name, housename)

    def check_user(self, name, password, housename, role):
        q = "SELECT * FROM users WHERE name = ? AND password = ? AND housename = ? AND role = ?"
        self.c.execute(q, (name, password, housename, role))
        result = self.c.fetchone()
        return True if result else False

    def check_user_exists(self, name):
        q = "SELECT * FROM users WHERE name = ?"
        self.c.execute(q, (name,))
        return True if self.c.fetchone() else False

    def housename_exists(self, housename):
        q = "SELECT * FROM users WHERE housename = ? "
        self.c.execute(q, (housename,))
        return True if self.c.fetchone() else False

    def check_email(self, email):
        q = "SELECT * FROM users WHERE email = ?"
        self.c.execute(q, (email,))
        return True if self.c.fetchone() else False

    def check_pending_role(self, name, password, housename):
        q = "SELECT * FROM users WHERE name = ? AND password = ? AND housename = ? AND role LIKE '%Pending%'"
        self.c.execute(q, (name, password, housename))
        return True if self.c.fetchone() else False

    def convert(self, fetchall):
        r = []
        for i in fetchall:
            r1 = {}
            r1['id'] = i[0]
            r1['username'] = i[1]
            r1['password'] = i[2]
            r1['housename'] = i[3]
            r1['role'] = i[4]
            r1['email'] = i[5]
            r.append(r1)
        return r

    def get_users(self):
        q = "SELECT * FROM users"
        self.c.execute(q)
        return self.convert(self.c.fetchall())

    def get_users_housername(self, housename):
        q = "SELECT * FROM users WHERE housename = ?"
        self.c.execute(q, (housename,))
        return self.convert(self.c.fetchall())

    def get_pending_users_housername(self, housename):
        q = "SELECT * FROM users WHERE housename = ? AND role LIKE '%Pending%'"
        self.c.execute(q, (housename,))
        return self.convert(self.c.fetchall())

    def get_approved_users_housername(self, housename):
        # get users where role dont start with Pending
        q = "SELECT * FROM users WHERE housename = ? AND role NOT LIKE '%Pending%'"
        self.c.execute(q, (housename,))
        result = self.convert(self.c.fetchall())
        # print('result', result)
        return result

    def username_housename_exits(self, username, housename):
        q = "SELECT * FROM users WHERE name = ? AND housename = ?"
        self.c.execute(q, (username, housename))
        return True if self.c.fetchone() else False


class UnitData:
    def __init__(self, db_name):
        if not (".db" in db_name or ".sqlite3" in db_name):
            db_name = db_name + '.db'
        self.db_name = db_name

        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.db.cursor()

        # table for units, cols are: id, name(username-housename), year,month,day,total_unit
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS units(id INTEGER PRIMARY KEY AUTOINCREMENT,name STRING,year INTEGER,month INTEGER,day INTEGER,total_unit REAL,total_ammount REAL,per_unit REAL)")

    def insert_unit(self, username, housename, year, month, day, total_unit, total_ammount, per_unit):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        day = int(day)
        total_unit = float(total_unit)
        total_ammount = float(total_ammount)
        per_unit = float(per_unit)

        # check if name and month and year already exists
        q = "SELECT * FROM units WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        print('result unit check', self.c.fetchone())
        if self.c.fetchone():
            # update if already exists
            q = "UPDATE units SET day = ?, total_unit = ?, total_ammount = ?, per_unit = ? WHERE name = ? AND year = ? AND month = ?"
            self.c.execute(q, (day, total_unit, total_ammount,
                           per_unit, name, year, month))
        else:
            # insert if not exists
            q = "INSERT INTO units(name,year,month,day,total_unit,total_ammount,per_unit) VALUES(?,?,?,?,?,?,?)"
            self.c.execute(q, (name, year, month, day,
                           total_unit, total_ammount, per_unit))
        self.db.commit()

    def delete_all_units(self, username, housename):
        """ delete all unit data of a user """
        name = username + '-' + housename
        q = "DELETE FROM units WHERE name = ?"
        self.c.execute(q, (name,))
        self.db.commit()

    def delete_unit(self, username, housename, year, month):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        q = "DELETE FROM units WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))

    def convert(self, fetchall):
        r = []
        for i in fetchall:
            r1 = {}
            r1['id'] = i[0]
            r1['name'] = i[1]
            r1['year'] = i[2]
            r1['month'] = i[3]
            r1['day'] = i[4]
            r1['total_unit'] = i[5]
            r1['total_ammount'] = i[6]
            r1['per_unit'] = i[7]
            r.append(r1)
        return r

    def get_units(self, username, housename):
        name = username + '-' + housename
        q = "SELECT * FROM units WHERE name = ?"
        self.c.execute(q, (name,))
        result = self.c.fetchall()
        return self.convert(result)

    def get_units_date(self, housename, month, year):
        name = f"%{housename}"
        q = "SELECT * FROM units WHERE name LIKE ? AND month = ? AND year = ?"
        self.c.execute(q, (name, month, year))
        result = self.c.fetchall()
        return self.convert(result)

    def get_previous_month_unit(self, username, housename, current_year, current_month):
        name = username + '-' + housename
        print(
            f'username {username} housename {housename} current_year {current_year} current_month {current_month}')
        month = int(current_month) - 1
        q = "SELECT total_unit FROM units WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, current_year, month))
        result = self.c.fetchone()
        return result[0] if result else 0

    def edit_unit(self, username, housename, year, month, total_unit, total_amount, per_unit):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        total_unit = float(total_unit)
        total_amount = float(total_amount)
        per_unit = float(per_unit)

        # check if name and month and year already exists
        q = "SELECT * FROM units WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        print('result unit check', self.c.fetchone())
        if self.c.fetchone():
            # update if already exists
            q = "UPDATE units SET total_unit = ?, total_ammount = ?, per_unit = ? WHERE name = ? AND year = ? AND month = ?"
            self.c.execute(q, (total_unit, total_amount,
                               per_unit, name, year, month))
        else:
            # insert if not exists
            q = "INSERT INTO units(name,year,month,total_unit,total_ammount,per_unit) VALUES(?,?,?,?,?,?)"
            self.c.execute(
                q, (name, year, month, total_unit, total_amount, per_unit))
        self.db.commit()


class BillData:
    def __init__(self, db_name):
        if not (".db" in db_name or ".sqlite3" in db_name):
            db_name = db_name + '.db'
        self.db_name = db_name

        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.db.cursor()

        # table for bills, cols are: id, name(username-housename), year,month,day,total_bill
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT,name STRING,year INTEGER,month INTEGER,total_units ,previous_month_units REAL, used_units REAL, unit_price REAL, extra_units REAL)")

    def insert_bill(self, username, housename, year, month, total_units, previous_month_units, used_units, unit_price, extra_units):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        total_units = float(total_units)
        previous_month_units = float(previous_month_units)
        used_units = float(used_units)
        unit_price = float(unit_price)
        extra_units = float(extra_units)

        # check if name and month and year already exists
        q = "SELECT * FROM bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        print('result bill check', self.c.fetchone())
        if self.c.fetchone():
            # update if already exists
            q = "UPDATE bills SET total_units = ?, previous_month_units = ?, used_units = ?, unit_price = ?, extra_units = ? WHERE name = ? AND year = ? AND month = ?"
            self.c.execute(q, (total_units, previous_month_units,
                           used_units, unit_price, extra_units, name, year, month))
        else:
            # insert if not exists
            q = "INSERT INTO bills(name,year,month,total_units,previous_month_units,used_units,unit_price,extra_units) VALUES(?,?,?,?,?,?,?,?)"
            self.c.execute(q, (name, year, month, total_units,
                           previous_month_units, used_units, unit_price, extra_units))
        self.db.commit()

    def convert(self, result):
        r = []
        for i in result:
            r1 = {}
            r1['id'] = i[0]
            r1['name'] = i[1]
            r1['year'] = i[2]
            r1['month'] = i[3]
            r1['total_units'] = i[4]
            r1['previous_month_units'] = i[5]
            r1['used_units'] = i[6]
            r1['unit_price'] = i[7]
            r1['extra_units'] = i[8]
            r.append(r1)
        return r

    def convert_one(self, result):
        if result:
            r = {}
            r['id'] = result[0]
            r['name'] = result[1]
            r['year'] = result[2]
            r['month'] = result[3]
            r['total_units'] = result[4]
            r['previous_month_units'] = result[5]
            r['used_units'] = result[6]
            r['unit_price'] = result[7]
            r['extra_units'] = result[8]
            return r
        else:
            return None

    def delete_bill(self, username, housename, year, month):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        q = "DELETE FROM bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        self.db.commit()

    def delete_all_bills(self, username, housename):
        name = username + '-' + housename
        q = "DELETE FROM bills WHERE name = ?"
        self.c.execute(q, (name,))
        self.db.commit()

    def edit_biil(self, username, housename, year, month, total_units, previous_month_units, used_units, unit_price, extra_units):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        total_units = float(total_units)
        previous_month_units = float(previous_month_units)
        used_units = float(used_units)
        unit_price = float(unit_price)
        extra_units = float(extra_units)
        q = "UPDATE bills SET total_units = ?, previous_month_units = ?, used_units = ?, unit_price = ?, extra_units = ? WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (total_units, previous_month_units,
                       used_units, unit_price, extra_units, name, year, month))
        self.db.commit()

    def get_bills(self, username, housename):
        name = username + '-' + housename
        q = "SELECT * FROM bills WHERE name = ?"
        self.c.execute(q, (name,))
        result = self.c.fetchall()
        return self.convert(result)

    def get_bill(self, username, housename, year, month):
        name = username + '-' + housename
        q = "SELECT * FROM bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        result = self.c.fetchone()
        return self.convert_one(result)

    def get_bills_date(self, housename, month, year):
        name = f"%{housename}"
        q = "SELECT * FROM bills WHERE name LIKE ? AND month = ? AND year = ?"
        self.c.execute(q, (name, month, year))
        result = self.c.fetchall()
        return self.convert(result)

    def get_user_bills(self, username, housename):
        name = username + '-' + housename
        q = "SELECT * FROM bills WHERE name = ?"
        self.c.execute(q, (name,))
        result = self.c.fetchall()
        return self.convert(result)


def edit_bill_units(username, housename, year, month, total_units, previous_month_units, used_units, unit_price, extra_units, total_ammount):
    custom_print(f'total_units: {total_units} previous_month_units: {previous_month_units} used_units: {used_units} unit_price: {unit_price} extra_units: {extra_units} total_ammount: {total_ammount}', color='red')

    units = UnitData(UNITDATA_PATH)
    units.edit_unit(username=username, housename=housename, year=year, month=month,
                    total_unit=total_units, total_amount=total_ammount, per_unit=unit_price)

    bills = BillData(BILLDATA_PATH)
    bills.edit_biil(username=username, housename=housename, year=year, month=month, total_units=total_units,
                    previous_month_units=previous_month_units, used_units=used_units, unit_price=unit_price, extra_units=extra_units)


class WaterBill:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self.db = sqlite3.connect(db_name)
        self.c = self.db.cursor()

        # table cols name(username+housename), year, month, amount
        q = "CREATE TABLE IF NOT EXISTS water_bills(name TEXT, year INTEGER, month INTEGER, amount REAL)"
        self.c.execute(q)
        self.db.commit()

    def convert(self, result):
        print('result', result)
        r = []
        for i in result:
            r1 = {}
            r1['name'] = i[0]
            r1['year'] = i[1]
            r1['month'] = i[2]
            r1['amount'] = i[3]
            r.append(r1)
        return r

    def convert_one(self, result):
        if result:
            r = {}
            r['name'] = result[0]
            r['year'] = result[1]
            r['month'] = result[2]
            r['amount'] = result[3]
            return r
        else:
            return None

    def add_bill(self, username, housename, year, month, amount):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        amount = float(amount)

        # check if record exist
        q = "SELECT * FROM water_bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        result = self.c.fetchone()
        if result:
            q = "UPDATE water_bills SET amount = ? WHERE name = ? AND year = ? AND month = ?"
            self.c.execute(q, (amount, name, year, month))
        else:
            q = "INSERT INTO water_bills VALUES (?, ?, ?, ?)"
            self.c.execute(q, (name, year, month, amount))
        self.db.commit()

    def get_bills(self, username, housename):
        name = username + '-' + housename
        q = "SELECT * FROM water_bills WHERE name = ?"
        self.c.execute(q, (name,))
        result = self.c.fetchall()
        return self.convert(result)

    def get_bill(self, username, housename, year, month):
        name = username + '-' + housename
        q = "SELECT * FROM water_bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        result = self.c.fetchone()
        return self.convert_one(result)

    def edit_bill(self, username, housename, year, month, amount):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        amount = float(amount)
        q = "UPDATE water_bills SET amount = ? WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (amount, name, year, month))
        self.db.commit()

    def get_bill_date(self, username, housename, month, year):
        name = username + '-' + housename
        q = "SELECT * FROM water_bills WHERE name = ? AND month = ? AND year = ?"
        self.c.execute(q, (name, month, year))
        result = self.c.fetchone()
        return self.convert_one(result)

    def delete_bill(self, username, housename, year, month):
        name = username + '-' + housename
        year = int(year)
        month = int(month)
        q = "DELETE FROM water_bills WHERE name = ? AND year = ? AND month = ?"
        self.c.execute(q, (name, year, month))
        self.db.commit()

    def total_bill(self, housename, month, year):
        name = f"%{housename}"
        q = "SELECT SUM(amount) FROM water_bills WHERE name LIKE ? AND month = ? AND year = ?"
        self.c.execute(q, (name, month, year))
        result = self.c.fetchone()
        return result[0]


def getUsersWaterBill(username, housename, month, year):
    waterdata = WaterBill(WATERDATA_PATH)

    q = "SELECT * FROM water_bills WHERE name LIKE ? AND month = ? AND year = ?"
    name = f"%{housename}"
    waterdata.c.execute(q, (name, month, year))
    result = waterdata.convert(waterdata.c.fetchall())

    userdata = UserData(USERDATA_PATH)
    users = userdata.get_approved_users_housername(housename=housename)
    return_users = []
    for user in users:
        for bill in result:
            if user['username'] == bill['name'].split('-')[0]:
                user['water_bill'] = bill
        return_users.append(user)

    return return_users

def get_apk_path():
    url = "https://github.com/shhossain/electricbillsfullapp/releases/latest"
    # get class .Box-row a href
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    link = soup.find(class_='Box-row')
    link = link.find('a')
    link = link['href']

    if link.startswith('/'):
        link = 'https://github.com' + link
    
    return link

if __name__ == '__main__':
    db = UnitData('units')
    print(db.get_units_date('villa', 5, 2022))
