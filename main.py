from flask import Flask, request,  jsonify, send_file, redirect
import requests
# from helper_file import Novels,convert,convert_novels
from bill_helper import BillData, UnitData, UserData, WaterBill, BILLDATA_PATH, UNITDATA_PATH, USERDATA_PATH, WATERDATA_PATH, custom_print, edit_bill_units, getUsersWaterBill,get_apk_path
from flask_cors import CORS

# CONSTANTS
APP_VERSION = '1.2.0'
APK_PATH = 'S:\\Code\\flutter\electricbills\\build\\app\outputs\\flutter-apk\\app.apk'
EXE_PATH = 'S:\\Code\\flutter\\electricbills\\build\windows\\runner\\Release\\electricbills.exe'
APK_UPDATE_IGNORE = '1.2.0'
EXE_UPDATE_IGNORE = '1.2.0'


class Compare:
    small = 0
    equal = 1
    large = 2


def versionCompare(v1, v2):
    # This will split both the versions by '.'
    arr1 = v1.split(".")
    arr2 = v2.split(".")
    n = len(arr1)
    m = len(arr2)

    # converts to integer from string
    arr1 = [int(i) for i in arr1]
    arr2 = [int(i) for i in arr2]

    # compares which list is bigger and fills
    # smaller list with zero (for unequal delimiters)
    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    # returns 1 if version 1 is bigger and -1 if
    # version 2 is bigger and 0 if equal
    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            return Compare.large
        elif arr2[i] > arr1[i]:
            return Compare.small
    return Compare.equal

# return update available and if update is ignoreable


def check_update(app_version, platform):
    ignore_version = APK_UPDATE_IGNORE if platform == 'android' else EXE_UPDATE_IGNORE if platform == 'windows' else None

    if ignore_version is None:
        return False, False

    compareWithCurrent = versionCompare(APP_VERSION, app_version)
    compareWithIgnore = versionCompare(app_version, ignore_version)

    updateAvailable = False
    updateIgnoreable = False

    if compareWithCurrent == Compare.large and compareWithIgnore == Compare.large:
        updateAvailable = True
        updateIgnoreable = True
    elif compareWithCurrent == Compare.large and compareWithIgnore == Compare.equal:
        updateAvailable = True
        updateIgnoreable = True
    elif compareWithCurrent == Compare.large and compareWithIgnore == Compare.small:
        updateAvailable = True
        updateIgnoreable = False

    return updateAvailable, updateIgnoreable


# from flask_cors import CORS
app = Flask(__name__)

# db_name = "/home/sh0338/mysite/novels.db"


# novels = Novels(db_name)


CORS(app)


# def unparse(url):
#     url = url.replac('%3A', ':').replace('%2F', '/').replace('%3F', '?').replace('%3D', '=').replace('%26', '&').replace('%23', '#').replace('%20', ' ').replace('%22', '"').replace('%27', "'").replace('%3C', '<').replace('%3E', '>').replace('%40', '@').replace('%24', '$').replace('%7B', '{').replace('%7D', '}').replace(
#         '%7C', '|').replace('%5C', '\\').replace('%5E', '^').replace('%5B', '[').replace('%5D', ']').replace('%60', '`').replace('%3B', ';').replace('%2B', '+').replace('%2D', '-').replace('%2E', '.').replace('%5F', '_').replace('%7E', '~').replace('%20', ' ').replace('%2A', '*').replace('%25', '%').replace("+", " ")
#     return url


# @app.route('/api/novel/<url>', methods=['GET', 'POST'])
# def novel_url(url):
#     url = unparse(url)
#     novel = novels.get_novel(url)
#     return jsonify(convert(novel))


# @app.route('/api/search/<query>')
# def search(query):
#     query = unparse(query)
#     all_novels = novels.search_novel(query)
#     return jsonify(convert_novels(all_novels))


# @app.route('/api/show', methods=["POST"])
# def show():
#     data = request.get_json()
#     if data is None:
#         data = request.form
#     what = data["what"]
#     value = data["value"]
#     order = data["order"]
#     orderby = data["orderby"]
#     status = data["status"]
#     page = data["page"]
#     limit = data["limit"]

#     page = int(page)
#     limit = int(limit)

#     all_novels = novels.show_novels(
#         what=what, value=value, order=order, orderby=orderby, status=status, page=page, limit=limit)
#     return jsonify(convert_novels(all_novels))


@app.route("/")
def home():
    return "Hello Word"


# errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'msg': 'Not found'})


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'msg': 'Sorry, server error'})


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'msg': 'Bad request'})


@app.route('/api/user/add', methods=['POST'])
def add_user():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    email = data.get('email')

    if not username or not password or not housename or not role or not email:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'email'}"})
    elif userdata.username_housename_exits(username, housename):
        return jsonify({'success': False, 'msg': f"'{username}' already exists"})
    elif userdata.housename_exists(housename):
        role = f"{role} Pending"
    elif userdata.check_email(email):
        return jsonify({'success': False, 'msg': f"'{email}' already exists"})

    userdata.insert_user(username, password, housename, role, email)
    success = True if role.find('Pending') == -1 else False
    msg = 'Registered successfully' if success else 'Registered successfully, but pending approval'
    return jsonify({'success': success, 'msg': msg})


@app.route('/api/user', methods=['POST'])
def check_user():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    check_user1 = userdata.check_user(name=username, password=password,
                                      housename=housename, role=role)
    check_user2 = userdata.check_user(
        name=username, password=password, housename=housename, role='Editor')
    if check_user1 or check_user2:
        return jsonify({'success': True, 'msg': 'Login successful'})
    elif userdata.check_pending_role(username, password, housename):
        return jsonify({'success': False, 'msg': 'Your role is pending. Please wait for approval'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


@app.route('/api/user/editor', methods=['POST'])
def add_user_editor():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    add_username = data.get('add_username')
    add_password = data.get('add_password')
    add_housename = data.get('add_housename')
    add_role = data.get('add_role')

    if not editor_username or not editor_password or not editor_housename or not add_username or not add_password or not add_housename or not add_role:
        return jsonify({'success': False,
                        'msg': f"Missing {'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'add_username' if not add_username else 'add_password' if not add_password else 'add_housename' if not add_housename else 'add_role' if not add_role else 'add_role'}"})
    elif userdata.check_user(name=editor_username, password=editor_password, housename=editor_housename, role='Editor'):
        add_email = f"{add_username}@{add_housename}.com"
        if userdata.check_user(add_username, add_password, add_housename, add_role):
            return jsonify({'success': False, 'msg': f"'{add_username}' already exists"})
        else:
            userdata.insert_user(add_username, add_password,
                                 add_housename, add_role, add_email)
            return jsonify({'success': True, 'msg': 'User added successfully'})
    else:
        return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


@app.route('/api/user/delete', methods=['POST'])
def delete_user():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    if not username or not password or not housename or not role or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})
    elif not userdata.check_user(name=editor_username, password=editor_password, housename=editor_housename,
                                 role='Editor'):
        return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})
    elif userdata.check_user(name=username, password=password, housename=housename, role='Editor'):
        return jsonify({'success': False, 'msg': 'You are not authorized to delete this user'})
    elif userdata.check_user(name=username, password=password, housename=housename, role=role):
        userdata.delete_user(username, housename)
        return jsonify({'success': True, 'msg': 'User deleted successfully'})


@app.route('/api/users', methods=['POST'])
def get_users():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    housename = data.get('housename')
    role = data.get('role')
    password = data.get('password')
    action = data.get('action')

    if userdata.check_user(username, password, housename, role):
        if str(role).lower() == 'editor':
            return users(username, password, housename, role, action)
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


def users(username, password, housename, role, action):
    userdata = UserData(USERDATA_PATH)

    if action == "get_users":
        return jsonify({'success': True, 'users': userdata.get_approved_users_housername(housename)})
    elif action == "get_pending_users":
        return jsonify({'success': True, 'users': userdata.get_pending_users_housername(housename)})


@app.route("/api/unit/add", methods=['POST'])
def add_unit():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')
    total_units = data.get('total_units')
    total_ammount = data.get('total_amount')
    per_unit = data.get('per_unit')
    action = data.get('action')

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    if not username or not password or not housename or not role or not month or not year or not day or not total_units or not total_ammount or not per_unit or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else 'total_units' if not total_units else 'total_ammount' if not total_ammount else 'per_unit' if not per_unit else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})

    elif userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        if userdata.check_user(username, password, housename, role):
            return unit(username, password, housename, role, month, year, day, total_units, total_ammount, per_unit,
                        action)
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


@app.route("/api/unit/get", methods=['POST'])
def get_unit():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')
    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')
    action = data.get('action')

    if not username or not password or not housename or not role or not month or not year or not day or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})

    elif userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        if userdata.check_user(username, password, housename, role):
            return unit(username, password, housename, role, month, year, day, action=action)
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


def unit(username, password, housename, role, month, year, day, total_units=0, total_ammount=0, per_unit=0,
         action=None):
    unitdata = UnitData(UNITDATA_PATH)
    if action == 'add_unit':
        unitdata.insert_unit(username, housename, year,
                             month, day, total_units, total_ammount, per_unit)
        return jsonify({'success': True, 'msg': 'Unit added successfully'})
    elif action == 'get_units':
        return jsonify({'success': True, 'msg': unitdata.get_units(username, housename)})
    elif action == 'prev_units':
        return jsonify({'success': True, 'msg': unitdata.get_previous_month_unit(username, housename, year, month)})
    elif action == 'get_units_date':
        return jsonify({'success': True, 'msg': unitdata.get_units_date(housename, month, year)})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


@app.route("/api/bill/add", methods=['POST'])
def add_bill():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    # custom_print('/api/bill/add data', data,color='blue')
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')
    total_units = data.get('total_units')
    total_ammount = data.get('total_amount')
    per_unit = data.get('per_unit')
    previous_month_unit = data.get('prev_month_unit')
    used_unit = data.get('used_unit')
    extra_unit = data.get('extra_unit')
    extra_unit = extra_unit if extra_unit else 0

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    if not username or not password or not housename or not role or not month or not year or not day or not total_units or not total_ammount or not per_unit or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else 'total_units' if not total_units else 'total_ammount' if not total_ammount else 'per_unit' if not per_unit else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})

    elif userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        if userdata.check_user(username, password, housename, role):
            return bill(username=username, password=password, housename=housename, role=role, month=month, year=year,
                        day=day, total_units=total_units, total_ammount=total_ammount, per_unit=per_unit,
                        previous_month_unit=previous_month_unit, used_unit=used_unit, extra_units=extra_unit,
                        action='add_bill')
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})


@app.route("/api/bill/get", methods=['POST'])
def get_bill():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')

    if not username or not password or not housename or not role or not month or not year or not day:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else ''}"})

    elif userdata.check_user(username, password, housename, role):
        return bill(username, password, housename, role, month, year, day, action='get_bill')
    elif userdata.check_user(username, password, housename, 'Editor'):
        return bill(username, password, housename, 'Editor', month, year, day, action='get_bill')

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


# get bills


@app.route("/api/bill/get_bills", methods=['POST'])
def get_bills():
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')
    action = data.get('action')

    # custom_print('/api/bill/get_bills request.form: ', data,color='green')

    if not username or not password or not housename or not role or not month or not year or not day:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else ''}"})

    elif userdata.check_user(name=username, password=password, housename=housename, role=role):
        if role == 'Editor':
            return bill(username, password, housename, role, month, year, day, action=action)
        elif role == 'Viewer':
            return bill(username, password, housename, role, month, year, day, action='get_bills')
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    elif userdata.check_user(name=username, password=password, housename=housename, role='Editor'):
        if role == 'Editor':
            return bill(username, password, housename, role, month, year, day, action=action)
        elif role == 'Viewer':
            return bill(username, password, housename, role, month, year, day, action='get_bills')
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


# delete bill
@app.route("/api/bill/delete", methods=['POST'])
def delete_bill():
    # onlt editor can delete bill
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    if not username or not password or not housename or not role or not month or not year or not day or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})
    elif userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        if userdata.check_user(username, password, housename, role):
            return bill(username=username, password=password, housename=housename, role=role, month=month, year=year,
                        day=day, action='delete_bill')
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})


# edit bill
@app.route("/api/bill/edit", methods=['POST'])
def edit_bill():
    # only editor can edit bill
    userdata = UserData(USERDATA_PATH)

    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    day = data.get('day')
    total_units = data.get('total_units')
    total_ammount = data.get('total_amount')
    per_unit = data.get('per_unit')
    previous_month_unit = data.get('prev_month_unit')
    used_unit = data.get('used_unit')
    extra_unit = data.get('extra_unit')
    extra_unit = extra_unit if extra_unit else 0

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    custom_print('/api/bill/edit request.form: ', data, color='green')

    if not username or not password or not housename or not role or not month or not year or not day or not editor_username or not editor_password or not editor_housename:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year' if not year else 'day' if not day else 'editor_username' if not editor_username else 'editor_password' if not editor_password else 'editor_housename' if not editor_housename else 'editor_housename'}"})
    elif userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        if userdata.check_user(username, password, housename, role):
            return bill(username=username, password=password, housename=housename, role=role, month=month, year=year,
                        day=day, action='edit_bill', total_units=total_units, total_ammount=total_ammount, per_unit=per_unit,
                        previous_month_unit=previous_month_unit, used_unit=used_unit, extra_units=extra_unit)
        else:
            return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


def bill(username, password, housename, role, month, year, day, total_units=0, total_ammount=0, per_unit=0,
         previous_month_unit=0, used_unit=0, action=None, extra_units=0):
    billdata = BillData(BILLDATA_PATH)

    if action == 'add_bill':
        billdata.insert_bill(username=username, housename=housename, year=year, month=month, total_units=total_units,
                             unit_price=per_unit, previous_month_units=previous_month_unit, used_units=used_unit,
                             extra_units=extra_units)
        return jsonify({'success': True, 'msg': 'Bill added successfully'})
    elif action == 'get_bills':
        data = billdata.get_user_bills(username, housename)
        # custom_print('/api/bill/get_bills data: ', data,color='blue')
        return jsonify({'success': True, 'msg': data})
    elif action == "get_bills_date":
        data = billdata.get_bills_date(housename, month, year)
        success = True if data else False
        data = 'No bill found' if not data else data
        # custom_print('/api/bill/get_bills_date data: ', data,color='blue')
        return jsonify({'success': success, 'msg': data})
    elif action == 'delete_bill':
        billdata.delete_bill(
            username=username, housename=housename, year=year, month=month)
        return jsonify({'success': True, 'msg': 'Bill deleted successfully'})
    elif action == 'edit_bill':
        edit_bill_units(username=username, housename=housename, year=year, month=month, total_units=total_units,
                        unit_price=per_unit, previous_month_units=previous_month_unit, used_units=used_unit,
                        extra_units=extra_units, total_ammount=total_ammount)
        return jsonify({'success': True, 'msg': 'Bill edited successfully'})
    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


@app.route("/api/update", methods=['POST'])
def update_available():
    data = request.form
    current_version = data.get('current_version')
    os = data.get('os')
    custom_print('/api/update request.form: ', data, color='green')

    if not current_version or not os:
        return jsonify({'success': False,
                        'msg': f"Missing {'current_version' if not current_version else 'os' if not os else 'os'}"})
    else:
        isUpdateAvailable = check_update(current_version, os)
        updateAvailable = isUpdateAvailable[0]
        ignoreAble = isUpdateAvailable[1]
        msg = 'Update available' if isUpdateAvailable else 'No update available'
        return jsonify({'success': True, 'msg': msg, 'updateAvailable': updateAvailable, 'ignoreAble': ignoreAble, 'latestVersion': APP_VERSION})




@app.route("/api/water/get_water_bill/<result>", methods=['POST'])
def get_water_bill(result):
    action = 'get_bill'
    if result == 'all':
        action = 'get_bills'

    userdata = UserData(USERDATA_PATH)
    data = request.form
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    month = data.get('month')
    year = data.get('year')
    custom_print('/api/water/get_water_bill request.form: ',
                 data, color='green')

    if not username or not password or not housename or not role or not month or not year:
        return jsonify({'success': False,
                        'msg': f"Missing {'username' if not username else 'password' if not password else 'housename' if not housename else 'role' if not role else 'month' if not month else 'year'}"})
    elif userdata.check_user(username, password, housename, role):
        return water(username=username, housename=housename, month=month, year=year,
                     action=action)
    elif userdata.check_user(username, password, housename, 'Editor'):
        return water(username=username, housename=housename, month=month, year=year,
                     action=action)

    return jsonify({'success': False, 'msg': 'Invalid username or password or Role'})


# water bill
@app.route("/api/water/<what>", methods=['POST'])
def add_water(what):
    action = what
    userdata = UserData(USERDATA_PATH)

    data = request.form
    # (username+housename), year, month, amount
    username = data.get('username')
    password = data.get('password')
    housename = data.get('housename')
    role = data.get('role')
    year = data.get('year')
    month = data.get('month')
    amount = data.get('amount')

    editor_username = data.get('editor_username')
    editor_password = data.get('editor_password')
    editor_housename = data.get('editor_housename')

    custom_print('/api/water/add request.form: ', action, data, color='green')

    if not username:
        return jsonify({'success': False, 'msg': 'Missing username'})

    if action == 'add_water' or action == 'delete_bill' or action == 'edit_bill' or action == 'total_bill' or action == 'get_users_water_bill':
        if not editor_username or not editor_password or not editor_housename:
            return jsonify({'success': False, 'msg': 'Missing editor username or password or housename'})

    if userdata.check_user(editor_username, editor_password, editor_housename, 'Editor'):
        return water(username=username, housename=editor_housename, year=year, month=month, amount=amount, action=action)

    return jsonify({'success': False, 'msg': 'You don\'t have permission to access this endpoint'})


def water(username, housename, year=2002, month=1, amount=1000, action=None):
    waterdata: WaterBill = WaterBill(WATERDATA_PATH)
    if action == 'add_water':  # editor
        waterdata.add_bill(username=username, housename=housename,
                           year=year, month=month, amount=amount)
        return jsonify({'success': True, 'msg': 'Water added successfully'})
    elif action == 'get_bills':  # editor
        data = waterdata.get_bills(username, housename)
        # custom_print('/api/water/get_waters data: ', data,color='blue')
        return jsonify({'success': True, 'msg': data})
    elif action == 'get_bill':  # viewer
        data = waterdata.get_bill(username, housename, year, month)
        # custom_print('/api/water/get_bill data: ', data,color='blue')
        return jsonify({'success': True, 'msg': data})
    elif action == 'get_bill_date':  # viewer
        data = waterdata.get_bill_date(username, housename, month, year)
        success = True if data else False
        data = 'No bill found' if not data else data
        # custom_print('/api/water/get_bills_date data: ', data,color='blue')
        return jsonify({'success': success, 'msg': data})
    elif action == 'delete_bill':  # editor
        waterdata.delete_bill(
            username=username, housename=housename, year=year, month=month)
        return jsonify({'success': True, 'msg': 'Water deleted successfully'})
    elif action == 'edit_bill':  # editor
        waterdata.edit_bill(username=username, housename=housename,
                            year=year, month=month, amount=amount)
        return jsonify({'success': True, 'msg': 'Water edited successfully'})
    elif action == 'total_bill':  # editor
        data = waterdata.total_bill(
            housename=housename, year=year, month=month)
        success = True if data else False
        data = '0' if not data else data
        return jsonify({'success': success, 'msg': data})
    elif action == 'get_users_water_bill':  # editor
        data = getUsersWaterBill(username, housename, month, year)
        custom_print('get_users_water_bill data: ', data, color='blue')
        return jsonify({'success': True, 'msg': data})

    return jsonify({'success': False, 'msg': 'Invalid action'})


# download app
@app.route("/api/download/<os>", methods=['GET'])
def download_apk(os):
    path = get_apk_path()
    if os == 'windows' or os == 'exe':
        path = EXE_PATH
    # redirect to the file path
    return redirect(path)


# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=80)
