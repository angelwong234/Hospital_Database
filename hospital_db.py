import flask
import sqlalchemy as sq
import xlrd
import csv
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker


app = flask.Flask(__name__)
app.secret_key = os.urandom(24)  ##encrypt cookie and decrypt later

oracle_connection_string = 'oracle+cx_oracle://{username}:{password}@{hostname}:{port}/{database}'

engine = sq.create_engine(
    oracle_connection_string.format(
        username=os.environ.get('HOSPITAL_USER'),
        password=os.environ.get('HOSPITAL_PASS'),
        hostname=os.environ.get('DB_HOST'),
        port='1521',
        database=os.environ.get('DB_SID')
    )
)

file = ''


def csv_from_excel(filename):
    data = xlrd.open_workbook(filename)
    sheet = data.sheet_by_name('Sheet1')
    global file
    file = filename[0:len(filename) - 4] + 'csv'
    csvfile = open(file, 'w')
    wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

    for numrow in range(sheet.nrows):
        wr.writerow(sheet.row_values(numrow))
    csvfile.close()


metadata = sq.MetaData(engine)
users = sq.Table('users', metadata, autoload=True, autoload_with=engine)
hospitals = sq.Table('hospitals', metadata, autoload=True, autoload_with=engine)
hospital_departments = sq.Table('hospital_departments', metadata, autoload=True, autoload_with=engine)
inpatients = sq.Table('inpatients', metadata, autoload=True, autoload_with=engine)
outpatients = sq.Table('outpatients', metadata, autoload=True, autoload_with=engine)
doctors = sq.Table('doctors', metadata, autoload=True, autoload_with=engine)
specializations = sq.Table('specializations', metadata, autoload=True, autoload_with=engine)
phone_numbers = sq.Table('phone_numbers', metadata, autoload=True, autoload_with=engine)
credentials = sq.Table('credentials', metadata, autoload=True, autoload_with=engine)
performs_inpatients = sq.Table('performs_inpatients', metadata, autoload=True, autoload_with=engine)
performs_outpatients = sq.Table('performs_outpatients', metadata, autoload=True, autoload_with=engine)
out_info = sq.Table('outpatient_procedure_info', metadata, autoload=True, autoload_with=engine)
in_info = sq.Table('inpatient_procedure_info', metadata, autoload=True, autoload_with=engine)
dep_info = sq.Table('department_info', metadata, autoload=True, autoload_with=engine)
logs = sq.Table('hospital_db_logs', metadata, autoload=True, autoload_with=engine)

connection = engine.connect()
inspector = sq.inspect(engine)

########################################################################################################################

# Signing up

########################################################################################################################


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    email = flask.request.form.get('email')
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    repassword = flask.request.form.get('repassword')
    code = flask.request.form.get('Code')
    Answer= '9234'

    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(users).filter(users.c.username.in_([username]), users.c.password.in_([password]))
    result = query.first()

    if flask.request.method == 'POST':
        print(password + " " + repassword)
        if result:
            flask.flash('You have already registered, please log in')
            return flask.redirect(flask.url_for('index'))

        elif email is None or username is None or password is None or code is None:
            flask.flash('Please fill in all of the forms')
            return flask.render_template('signup.html')
        elif code != Answer:
            flask.flash('Wrong code, please contact admin')
            return flask.render_template('signup.html')

        elif '@' not in email:
            flask.flash('Please enter a valid email')
            return flask.render_template('signup.html')
        elif password.strip() is repassword.strip():
            flask.flash('your passwords do not match')
            return flask.render_template('signup.html')
        else:
            adduser(email, username, password)
            return flask.redirect(flask.url_for('index'))

    return flask.render_template('signup.html')


@app.route('/adduser')
def adduser(email, username, password):
    import hashlib
    salt = "5ztih"
    db_password = password + salt
    hashed = hashlib.md5(db_password.encode()).hexdigest()
    # from passlib.hash import sha256_crypt
    # password=sha256_crypt.encrypt(password)
    user_i = sq.select([sq.func.max(users.c.user_id)])
    ResultProxy = connection.execute(user_i)
    user_index = ResultProxy.fetchall()
    if user_index[0][0] is None:
        index = 1
    else:
        index = user_index[0][0]+1
    query = sq.insert(users).values(user_id=index, email=email, username=username, password=hashed)
    connection.execute(query)
    index = index + 1
    flask.flash('You are being registered')


########################################################################################################################

# Login page

########################################################################################################################

@app.route('/', methods=['GET', 'POST'])
def start():
    if flask.request.method == 'POST':
        if flask.request.form.get('Admin Access'):
            return flask.redirect(flask.url_for('index'))
        if flask.request.form.get('Patient Access'):
            return flask.redirect(flask.url_for('query_options'))
    return flask.render_template('welcome_page.html')


@app.route('/login', methods=['GET', 'POST'])
def index():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')

    if flask.request.method == 'POST':
        flask.session.pop('username', None)
        result = check(username, password)
        if result:
            flask.session['username'] = flask.request.form['username']
            return flask.redirect(flask.url_for('boss'))
        else:
            flask.flash('Wrong username/password')
            return flask.render_template('login.html')
    return flask.render_template('login.html')


def check(username, password):
    Session = sessionmaker(bind=engine)
    s = Session()
    import hashlib
    salt = "5ztih"
    db_password = password + salt
    hashed = hashlib.md5(db_password.encode()).hexdigest()
    query = s.query(users).filter(users.c.username.in_([username]), users.c.password.in_([hashed]))
    result = query.first()
    return result


########################################################################################################################

# Admin-page

########################################################################################################################
@app.route('/boss', methods=['GET', 'POST'])
def boss():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        option = flask.request.form['options']
        print(option)
        if option.strip() == "Add Hospital":
            return flask.redirect(flask.url_for('addHospital')) 
        elif option == 'Delete Hospital':
            return flask.redirect(flask.url_for('deleteHospital')) 
        elif option == 'Update User':
            return flask.redirect(flask.url_for('updateuser')) 
        elif option == 'Delete User':
            return flask.redirect(flask.url_for('deleteuser')) 
        elif option == 'Add Department':
            return flask.redirect(flask.url_for('addDepartment')) 
        elif option == 'Update Department':
            return flask.redirect(flask.url_for('updatedepartment')) 
        elif option == 'Delete Department':
            return flask.redirect(flask.url_for('deletedepartment')) 
        elif option == 'Add Doctor':
            return flask.redirect(flask.url_for('addDoctor'))
        elif option == 'Delete Doctor':
            return flask.redirect(flask.url_for('deletedoctor'))
        elif option == 'Add Number':
            return flask.redirect(flask.url_for('addnum'))
        elif option == 'Update Number':
            return flask.redirect(flask.url_for('updatenum'))
        elif option == 'Delete Number':
            return flask.redirect(flask.url_for('deletenum'))
        elif option == 'Add Cred':
            return flask.redirect(flask.url_for('addcred'))
        elif option == 'Add Spec':
            return flask.redirect(flask.url_for('addspec'))
        elif option == 'Delete Review':
            return flask.redirect(flask.url_for('deletereview'))#Review 
        elif option == 'Add in':
            return flask.redirect(flask.url_for('addin')) 
        elif option == 'Update in':
            return flask.redirect(flask.url_for('updatein'))
        elif option == 'Delete in':
            return flask.redirect(flask.url_for('deletein'))
        elif option == 'Add out':
            return flask.redirect(flask.url_for('addout'))
        elif option == 'Update out':
            return flask.redirect(flask.url_for('updateout'))
        elif option == 'Delete out':
            return flask.redirect(flask.url_for('deleteout'))

    return flask.render_template('boss_page.html')


@app.route('/log', methods=['GET', 'POST'])
def log():
    # ht_log = None
    # name = 'Not working'
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))

    log_query = sq.select([logs])
    log_df = pd.DataFrame(connection.execute(log_query).fetchall())
    log_df.columns = ["Log ID", "Date of Change", "Table Changed", "Description"]
    log_df.index = log_df.index + 1
    get_logs = log_df.to_html()

    return flask.render_template('log.html', result=get_logs)


########################################################################################################################

# Patient-page
# The calling the different pages and getting the inputs, retrieving the information from the database and outputting
# on to the HTML page

########################################################################################################################


@app.route('/patient-portal', methods=['GET', 'POST'])
def query_options():
    if flask.request.method == 'POST':
        option = flask.request.form['option']
        # print(option)
        if option == "find":
            return flask.redirect(flask.url_for('doctor'))
        elif option == "cost":
            return flask.redirect(flask.url_for('cost'))
        elif option == "learn":
            return flask.redirect(flask.url_for('learn'))
        elif option == "department":
            return flask.redirect(flask.url_for('department'))
    return flask.render_template('patient_portal.html')


@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    result = None
    hosp_result = None
    proc_result = None
    # List of doctors
    doc_query = sq.select([doctors.columns.doctor_name])
    doc = pd.DataFrame(connection.execute(doc_query))
    doc_list = list(set(doc[0].tolist()))

    # List of hospitals
    hosp_query = sq.select([hospitals.columns.hospital_name])
    hosp = pd.DataFrame(connection.execute(hosp_query))
    hosp_list = list(set(hosp[0].tolist()))

    # List of procedures
    out_proc_query = sq.select([outpatients.columns.outpatient_procedure_name])
    out_procs = pd.DataFrame(connection.execute(out_proc_query))
    out_procs = list(set(out_procs[0].tolist()))

    in_proc_query = sq.select([inpatients.columns.inpatient_procedure_name])
    in_procs = pd.DataFrame(connection.execute(in_proc_query))
    in_procs = list(set(in_procs[0].tolist()))

    doc_print = ''
    hosp_print = ''
    proc_print = ''

    if flask.request.method == 'POST':
        doc_name = flask.request.form.get('Doctor')
        hosp_name = flask.request.form.get('Hospital')
        proc_name = flask.request.form.get('Procedure')

        if doc_name in doc_list:

            doc_print = "Dr. " + doc_name + "'s procedures are:"

            d_query = sq.select([out_info.columns.outpatient_procedure_name]). \
                    where(out_info.columns.doctor_name == doc_name)
            get_d_procs = pd.DataFrame(connection.execute(d_query).fetchall())

            d_i_query = sq.select([in_info.columns.inpatient_procedure_name]). \
                where(in_info.columns.doctor_name == doc_name)
            get_d_in_procs = pd.DataFrame(connection.execute(d_i_query).fetchall())

            if get_d_procs.empty and get_d_in_procs.empty:  # if doctor has no procedures
                doc_print = "No procedures are performed by Dr. " + doc_name

            else:
                get_d_procs = pd.concat([get_d_procs, get_d_in_procs], ignore_index=True)
                get_d_procs.columns = ["Procedure"]
                get_d_procs.index = get_d_procs.index + 1
                # get_d_procs.style.set_properties(**{'text-align': 'left'})
                result = get_d_procs.to_html()

        if hosp_name in hosp_list:

            hosp_print = "Procedures performed at " + hosp_name + " are:"

            h_query = sq.select([out_info.columns.outpatient_procedure_name]). \
                    where(out_info.columns.hospital_name == hosp_name)
            get_h_procs = pd.DataFrame(connection.execute(h_query).fetchall())

            if get_h_procs.empty:  # if hospital has no procedures
                hosp_print = "No procedures are performed at " + hosp_name

            else:
                get_h_procs.columns = ["Procedure"]
                get_h_procs.index = get_h_procs.index + 1
                hosp_result = get_h_procs.to_html()

        if proc_name in out_procs:
            proc_print = 'The outpatient procedure ' + proc_name + ' is peformed by these doctors:'
            out_query = sq.select([out_info.columns.doctor_name]).where(out_info.columns.outpatient_procedure_name == proc_name)
            get_out = pd.DataFrame(connection.execute(out_query).fetchall())

            if get_out.empty:
                proc_print = 'The outpatient procedure ' + proc_name + 'is not performed by any doctors'

            else:
                get_out.columns = ["Doctor"]
                get_out.index = get_out.index + 1
                proc_result = get_out.to_html()

        if proc_name in in_procs:
            proc_print = 'The inpatient procedure ' + proc_name + ' is peformed by these doctors:'

            in_query = sq.select([in_info.columns.doctor_name]).where(in_info.columns.inpatient_procedure_name == proc_name)
            get_in = pd.DataFrame(connection.execute(in_query).fetchall())
            get_in.columns = ["Doctor"]

            if get_in.empty:
                proc_print = 'The outpatient procedure ' + proc_name + 'is not performed by any doctors'

            else:
                get_in.columns = ["Doctor"]
                get_in.index = get_in.index + 1
                proc_result = get_in.to_html()

    return flask.render_template('doctor.html', doc_result=result, hosp_result=hosp_result, proc_result=proc_result,
                           doc_list=doc_list, hosp_list=hosp_list, name_proc=(out_procs + in_procs),
                           doc_print=doc_print, hosp_print=hosp_print, proc_print=proc_print)


@app.route('/cost', methods=['GET', 'POST'])
def cost():
    result = None
    name_proc = ''
    out_proc_query = sq.select([outpatients.columns.outpatient_procedure_name])
    out_procs = pd.DataFrame(connection.execute(out_proc_query))
    out_procs = list(set(out_procs[0].tolist()))

    in_proc_query = sq.select([inpatients.columns.inpatient_procedure_name])
    in_procs = pd.DataFrame(connection.execute(in_proc_query))
    in_procs = list(set(in_procs[0].tolist()))


    if flask.request.method == 'POST':
        proc_name = flask.request.form.get('Procedure')
        option = flask.request.form['option']

        name_proc = proc_name + ' is not listed'

        if proc_name in out_procs:
            name_proc = proc_name + ' is an outpatient procedure'
            if option == 'hospital':
                out_query = sq.select([out_info.columns.hospital_name, out_info.columns.outpatient_cost]).\
                    where(out_info.columns.outpatient_procedure_name == proc_name)
                get_out = pd.DataFrame(connection.execute(out_query).fetchall())
                get_out.columns = ["Hospital", "Average Cost of Procedure"]
                get_out.index = get_out.index + 1
                # '${:,.2f}'.format(1234.5)
                result = get_out.to_html()

            elif option == 'doctor':
                out_query = sq.select([out_info.columns.doctor_name, out_info.columns.outpatient_cost]).\
                    where(out_info.columns.outpatient_procedure_name == proc_name)
                get_out = pd.DataFrame(connection.execute(out_query).fetchall())
                get_out.columns = ["Doctor", "Average Cost of Procedure"]
                get_out.index = get_out.index + 1
                result = get_out.to_html()

            elif option == 'both':
                out_query = sq.select([out_info.columns.hospital_name, out_info.columns.doctor_name,
                                       out_info.columns.outpatient_cost]).where(out_info.columns.outpatient_procedure_name == proc_name)
                get_out = pd.DataFrame(connection.execute(out_query).fetchall())
                get_out.columns = ["Hospital", "Doctor", "Average Cost of Procedure"]
                get_out.index = get_out.index + 1
                result = get_out.to_html()

        elif proc_name in in_procs:
            name_proc = proc_name + ' is an inpatient procedure'
            if option == 'hospital':
                in_query = sq.select([in_info.columns.hospital_name, in_info.columns.inpatient_cost, in_info.columns.cost_of_stay]).\
                    where(in_info.columns.inpatient_procedure_name == proc_name)
                get_in = pd.DataFrame(connection.execute(in_query).fetchall())
                get_in.columns = ["Hospital", "Average Cost of Procedure", "Average Cost Per Night"]
                get_in.index = get_in.index + 1
                result = get_in.to_html()

            elif option == 'doctor':
                in_query = sq.select([in_info.columns.doctor_name, in_info.columns.inpatient_cost, in_info.columns.cost_of_stay]).\
                    where(in_info.columns.inpatient_procedure_name == proc_name)
                get_in = pd.DataFrame(connection.execute(in_query).fetchall())
                get_in.columns = ["Doctor", "Average Cost of Procedure", "Average Cost Per Night"]
                get_in.index = get_in.index + 1
                result = get_in.to_html()

            elif option == 'both':
                in_query = sq.select([in_info.columns.hospital_name, in_info.columns.doctor_name,
                                      in_info.columns.inpatient_cost, in_info.columns.cost_of_stay]).\
                    where(in_info.columns.inpatient_procedure_name == proc_name)
                get_in = pd.DataFrame(connection.execute(in_query).fetchall())
                get_in.columns = ["Hospital", "Doctor", "Average Cost of Procedure", "Average Cost Per Night"]
                get_in.index = get_in.index + 1
                result = get_in.to_html()

        # else: if proc_name does not exist

    return flask.render_template('cost.html', table=result, procs=(out_procs + in_procs), name_proc=name_proc)


@app.route('/learn-more', methods=['GET', 'POST'])
def learn():
    # result = request.form.get('Doctor')
    name = 'None selected'
    result = None
    result2 = None
    result3 = None
    # result4 = None
    if flask.request.method == 'POST':

        # Gets the user input of the doctors name and searches through the doctors table for the doctor id
        name = flask.request.form.get('Doctor')   # .title()  # makes it so string is title case (first letter is uppercase and rest is lowercase)
        query = sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == name)
        df = pd.DataFrame(connection.execute(query).fetchall())
        doctor_id = int(df.values[0][0])


        # Getting phone numbers
        phone_query = sq.select([phone_numbers.columns.phone_number]).where(phone_numbers.columns.doctor_id == doctor_id)
        get_phones = pd.DataFrame(connection.execute(phone_query).fetchall())

        if get_phones.empty:
            result = None
        else:
            # Converts phone numbers 8402012311 to (840)-201-2311
            get_phones = get_phones.astype(str)
            for phones, row in get_phones.iterrows():
                for v in row:
                    if len(v) == 10:  # if phone number is 10 numbers long
                        read_nums = "(" + v[:3] + ") " + v[3:6] + "-" + v[6:]
                        get_phones.at[phones, 0] = read_nums

            get_phones.columns = ["Phone Number"]
            get_phones.index = get_phones.index + 1
            result = get_phones.to_html()

        # Getting credentials
        cred_query = sq.select([credentials.columns.place_of_education]).where(credentials.columns.doctor_id == doctor_id)
        get_creds = pd.DataFrame(connection.execute(cred_query).fetchall())

        if get_creds.empty:
            result = None
        else:
            get_creds.columns = ["Place Of Education"]
            get_creds.index = get_creds.index + 1
            result2 = get_creds.to_html()

        # Getting specialization
        spec_query = sq.select([specializations.columns.specialization]).where(specializations.columns.doctor_id == doctor_id)
        get_specs = pd.DataFrame(connection.execute(spec_query).fetchall())
        if get_specs.empty:
            result = None
        else:
            get_specs.columns = ["Specialization"]
            get_specs.index = get_specs.index + 1
            result3 = get_specs.to_html()

    doc_query = sq.select([doctors.columns.doctor_name])
    docs = pd.DataFrame(connection.execute(doc_query))

    return flask.render_template('learn_more.html', name=name, table=result, table2=result2, table3=result3, doctors=docs[0].tolist())


@app.route('/department', methods=['GET', 'POST'])
def department():
    result = None
    trial = None

    dep_query = sq.select([dep_info.columns.department_name])
    dep = pd.DataFrame(connection.execute(dep_query))
    dep_list = list(set(dep[0].tolist()))

    dep_print = ''
    if flask.request.method == 'POST':
        dep_name = flask.request.form.get('Department')
        d_query = sq.select([dep_info.columns.hospital_name, dep_info.columns.department_name, dep_info.columns.ranking,
                             dep_info.columns.wait_time]).where(dep_info.columns.department_name == dep_name)

        get_deps = pd.DataFrame(connection.execute(d_query).fetchall())

        if get_deps.empty:  # if doctor has no procedures
            dep_print = "There is no information about the " + dep_name + " department"

        else:
            dep_print = "Ranking and wait times for the " + dep_name + " department"
            get_deps.columns = ["Hospital Name", "Department Name", "Department Ranking", "Average Wait Time (minutes)"]

            get_deps.index = get_deps.index + 1
            result = get_deps.to_html()

    return flask.render_template('department.html', dep_result=result, dep_list=dep_list, dep_print=dep_print, trial=trial)
########################################################################################################################

# Changes to Hospital

########################################################################################################################


@app.route('/addHospital', methods=['GET', 'POST'])
def addHospital():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        try:
            Hospital_Name = flask.request.form.get('Hospital Name')
            Street = flask.request.form.get('Street')
            Zipcode = flask.request.form.get('Zipcode')
            City = flask.request.form.get('City')
            State = flask.request.form.get('State')
        except:
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('addHospital'))

        if Hospital_Name == '' or Street.strip() == '' or Zipcode.strip() == '' or State.strip() == '':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('addHospital'))
        else:
            Session = sessionmaker(bind=engine)
            s = Session()
            query = s.query(hospitals).filter(hospitals.c.hospital_name.in_([Hospital_Name]),
                                              hospitals.c.street.in_([Street]), hospitals.c.zipcode.in_([Zipcode]))
            result = query.first()
            print(result)
            if result:
                flask.flash('This hospital already exists, you can update or make a new one')
                return flask.redirect(flask.url_for('addHospital'))
            else:
                addHosp(Hospital_Name, Street, Zipcode, City, State)
                return flask.redirect(flask.url_for('boss'))

    return flask.render_template('addHospital.html')


def addHosp(Hospital_Name, Street, Zipcode,City, State):

    stmt = sq.select([sq.func.max(hospitals.c.hospital_id)])
    ResultProxy = connection.execute(stmt)
    hospital_index = ResultProxy.fetchall()
    Hospital_Index=hospital_index[0][0]+1
    Zipcode = int(Zipcode)

    query = sq.insert(hospitals).values(hospital_id=Hospital_Index,
                                        hospital_name=Hospital_Name,
                                        street=Street,
                                        zipcode=Zipcode,
                                        city= City,
                                        state=State)
    connection.execute(query)
    flask.flash('Your table is being added')


@app.route('/deleteHospital', methods=['GET', 'POST'])
def deleteHospital():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital_Name = flask.request.form.get('Hospital')

        if Hospital_Name=='':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('deleteHospital'))
        else:
            hosp = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name==Hospital_Name)
            ResultProxy = connection.execute(hosp)
            hos_id = ResultProxy.fetchall()
            delHospital(hos_id[0][0], Hospital_Name)
            return flask.redirect(flask.url_for('boss'))

    hosp= sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    hospital = ResultProxy.fetchall()

    return flask.render_template('deleteHospital.html', hospital=hospital)


def delHospital(Hospital_ID, Hospital_Name):
    query = sq.delete(outpatients).where(outpatients.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    query = sq.delete(inpatients).where(inpatients.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    query = sq.delete(performs_inpatients).where(performs_inpatients.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    query = sq.delete(performs_outpatients).where(performs_outpatients.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    query = sq.delete(hospital_departments).where(hospital_departments.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    query = sq.delete(hospitals).where(hospitals.columns.hospital_id == Hospital_ID)
    results = connection.execute(query)
    flask.flash('The hospital: ' + Hospital_Name + " has been deleted.")





########################################################################################################################

# Changes to User

########################################################################################################################

@app.route('/updateuser', methods=['GET', 'POST'])
def updateuser():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        username= flask.request.form.get('User')
        usern = sq.select([users.columns.user_id]).where(users.columns.username == username)
        ResultProxy = connection.execute(usern)
        id = ResultProxy.fetchall()
        user_id = int(id[0][0])
        email = flask.request.form.get('email')
        if email == '' or username == '':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('updateuser'))
        else:
            user = sq.update(users).values(email=email)
            user = user.where(users.columns.user_id == user_id)
            ResultProxy = connection.execute(user)
            flask.flash('Your email has been updated')
            return flask.redirect(flask.url_for('boss'))
    user = sq.select([users.columns.username])
    ResultProxy = connection.execute(user)
    User = ResultProxy.fetchall()
    return flask.render_template('UpdateUser.html', User=User)



@app.route('/deleteuser', methods=['GET', 'POST'])
def deleteuser():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        username = flask.request.form.get('User')
        usern = sq.select([users.columns.user_id]).where(users.columns.username == username)
        ResultProxy = connection.execute(usern)
        id = ResultProxy.fetchall()
        user_id = int(id[0][0])
        if username == '':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('deleteuser'))
        else:
            user = sq.delete(users).where(users.columns.user_id == user_id)
            ResultProxy = connection.execute(user)
            flask.flash(username + " has been deleted")
            return flask.redirect(flask.url_for('boss'))
    user = sq.select([users.columns.username])
    ResultProxy = connection.execute(user)
    User = ResultProxy.fetchall()
    return flask.render_template('deleteuser.html', User=User)




########################################################################################################################

# Department

########################################################################################################################

@app.route('/addDepartment', methods=['GET', 'POST'])
def addDepartment():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital_Name = flask.request.form.get('Hospital')
        hosp = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital_Name)
        ResultProxy = connection.execute(hosp)
        hos_id = ResultProxy.fetchall()
        Hospital_ID = hos_id[0][0]
        Ranking = flask.request.form.get('Ranking')
        Department_Name = flask.request.form.get('Department_Name')
        Wait_Times = flask.request.form.get('Wait_Times')

        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(hospital_departments).filter(hospital_departments.c.department_name.in_([Department_Name]),
                                                     hospital_departments.c.hospital_id.in_([Hospital_ID]))
        result = query.first()

        if Ranking.strip() == '' or Department_Name == '' or Wait_Times.strip() == '':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('addDepartment'))
        else:
            Session = sessionmaker(bind=engine)
            s = Session()
            query = s.query(hospital_departments).filter(hospital_departments.c.department_name.in_([Department_Name]))
            result = query.first()
            if result:
                flask.flash('This department already exists, you can update or make a new one')
                return flask.redirect(flask.url_for('addDepartment'))
            else:
                addDept(Hospital_ID, Department_Name, Ranking, Wait_Times)
                return flask.redirect(flask.url_for('boss'))

    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    return flask.render_template('addDepartment.html', Hospital=Hospital)


def addDept(Hospital_ID, Department_Name, Ranking, Wait_Times):
    Ranking = float(Ranking)
    Wait_Times = int(Wait_Times)

    query = sq.insert(hospital_departments).values(hospital_id=Hospital_ID,
                                                   department_name=Department_Name,
                                                   ranking=Ranking,
                                                   wait_time=Wait_Times)
    connection.execute(query)
    flask.flash('Your department is being added')


@app.route('/updatedepartment', methods=['GET', 'POST'])
def updatedepartment():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':

        Hospital_Name = flask.request.form.get('Hospital')
        hosp = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital_Name)
        ResultProxy = connection.execute(hosp)
        hos_id = ResultProxy.fetchall()
        Hospital_ID = hos_id[0][0]
        Ranking = flask.request.form.get('Ranking')
        Department_Name = flask.request.form.get('Department_Name')
        Wait_Times = flask.request.form.get('Wait_Times')

        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(hospital_departments).filter(hospital_departments.c.department_name.in_([Department_Name]),
                                                     hospital_departments.c.hospital_id.in_([Hospital_ID]))
        result = query.first()

        if Ranking.strip() == '' or Department_Name == '' or Wait_Times.strip() == '':
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('updatedepartment'))
        elif not result:
            flask.flash('Department Does not exist')
            return flask.redirect(flask.url_for('updatedepartment'))
        else:
            department = sq.update(hospital_departments).values(wait_time=Wait_Times, ranking=Ranking)
            department = department.where(hospital_departments.c.department_name == Department_Name)
            department = department.where(hospital_departments.c.hospital_id == Hospital_ID)
            ResultProxy = connection.execute(department)
            flask.flash('Your department has been updated')
            return flask.redirect(flask.url_for('boss'))
    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    return flask.render_template('updatedepartment.html', Hospital=Hospital )




@app.route('/deletedepartment', methods=['GET', 'POST'])
def deletedepartment():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        try:
            Hospital_Name = flask.request.form.get('Hospital')
            hosp = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital_Name)
            ResultProxy = connection.execute(hosp)
            hos_id = ResultProxy.fetchall()
            Hospital_ID = hos_id[0][0]
            Department_Name = flask.request.form.get('Department_Name')

            Session = sessionmaker(bind=engine)
            s = Session()
            query = s.query(hospital_departments).filter(hospital_departments.c.department_name.in_([Department_Name]),
                                                         hospital_departments.c.hospital_id.in_([Hospital_ID]))
            result = query.first()
        except:
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('deletedepartment'))

        if not Department_Name.strip():
            flask.flash('You need to fill in all of the forms')
            return flask.redirect(flask.url_for('deletedepartment'))
        elif not result:
            flask.flash('Department Does not exist')
            return flask.redirect(flask.url_for('deletedepartment'))
        else:
            deldept(Hospital_ID, Department_Name, Hospital_Name)
            return flask.redirect(flask.url_for('boss'))
    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    return flask.render_template('deletedepartment.html', Hospital=Hospital )


def deldept(Hospital_ID, Department_Name, Hospital_Name):

    query = sq.delete(hospital_departments).where(hospital_departments.columns.hospital_id == Hospital_ID,
                                                  hospital_departments.columns.department_name== Department_Name)
    results = connection.execute(query)

    flask.flash('The department: ' + Department_Name + " has been deleted from "+ Hospital_Name)


########################################################################################################################

# doctors

########################################################################################################################


@app.route('/addDoctor', methods=['GET', 'POST'])
def addDoctor():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor=flask.request.form.get('Name')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(doctors).filter(doctors.c.doctor_name.in_([Doctor]))
        result = query.first()
        if result:
            flask.flash('Doctor is already in list')
            return flask.redirect(flask.url_for('addDoctor'))
        if Doctor == '' or Doctor is None :
            flask.flash('Need Doctors name')
            return flask.redirect(flask.url_for('addDoctor'))
        else:
            Doctor_i = sq.select([sq.func.max(doctors.c.doctor_id)])
            ResultProxy = connection.execute(Doctor_i)
            Doc_index = ResultProxy.fetchall()
            index = Doc_index[0][0] + 1
            query = sq.insert(doctors).values(doctor_id=index, doctor_name= Doctor)
            connection.execute(query)
            flask.flash('Doctor was added')
            return flask.redirect(flask.url_for('boss'))
    return flask.render_template('addDoctor.html')



@app.route('/deletedoctor', methods=['GET', 'POST'])
def deletedoctor():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Name = flask.request.form.get('Doctor')
        name= sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Name)
        ResultProxy = connection.execute(name)
        doc_id = ResultProxy.fetchall()
        Doctor_ID = doc_id[0][0]
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(doctors).filter(doctors.c.doctor_id.in_([Doctor_ID]))
        result = query.first()
        if not result:
            flask.flash('Doctor is not in the list')
            return flask.redirect(flask.url_for('deletedoctor'))
        if Name == '' or Name is None :
            flask.flash('Need Doctors name')
            return flask.redirect(flask.url_for('deletedoctor'))
        else:
            Session = sessionmaker(bind=engine)
            s = Session()
            query = s.query(doctors).filter(doctors.c.doctor_name.in_([Name]))
            result = query.first()
            if not result:
                flask.flash('This doctor does not exist, you need to add it')
                return flask.redirect(flask.url_for('deletedoctor'))
            else:
                deldoc(Doctor_ID, Name)
                return flask.redirect(flask.url_for('boss'))
    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('deletedoctor.html', Doctor=Doctor)


def deldoc(Doctor_ID, Doctor_Name):
    query = sq.delete(performs_inpatients).where(performs_inpatients.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)

    query = sq.delete(performs_outpatients).where(performs_outpatients.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)

    query = sq.delete(specializations).where(specializations.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)

    query = sq.delete(credentials).where(credentials.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)

    query = sq.delete(phone_numbers).where(phone_numbers.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)

    query = sq.delete(doctors).where(doctors.columns.doctor_id == Doctor_ID)
    results = connection.execute(query)


    flask.flash('The doctor:' + Doctor_Name+ ' has been deleted from all records')


########################################################################################################################

# Specialization- add

########################################################################################################################
@app.route('/addspec', methods=['GET', 'POST'])
def addspec():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor=flask.request.form.get('Doctor')
        ID = sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Doctor)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        spec=flask.request.form.get('spec')


        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(specializations).filter(specializations.c.doctor_id.in_([id[0][0]]),
                                                specializations.c.specialization.in_([spec]))
        result = query.first()

        print(result)
        if result:
            flask.flash('Specialization is already in list')
            return flask.redirect(flask.url_for('addspec'))
        if Doctor == '' or Doctor is None or spec=='' or spec is None :
            flask.flash('Need Doctors name and specialization')
            return flask.redirect(flask.url_for('addspec'))
        else:

            query = sq.insert(specializations).values(doctor_id=ID, specialization=spec)
            connection.execute(query)
            flask.flash('Specialization was added')
            return flask.redirect(flask.url_for('boss'))

    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('addspec.html', Doctor=Doctor)

########################################################################################################################

# Credentials - add

########################################################################################################################
@app.route('/addcred', methods=['GET', 'POST'])
def addcred():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor = flask.request.form.get('Doctor')
        ID = sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Doctor)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()

        POE = flask.request.form.get('POE')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(credentials).filter(credentials.c.doctor_id.in_([id[0][0]]),
                                            credentials.c.place_of_education.in_([POE]))
        result = query.first()

        if result:
            flask.flash('Credential is already in list')
            return flask.redirect(flask.url_for('addcred'))
        if Doctor == '' or Doctor is None or POE=='' or POE is None:
            flask.flash('Need Doctors name and credentials')
            return flask.redirect(flask.url_for('addcred'))
        else:

            query = sq.insert(credentials).values(doctor_id=ID, place_of_education=POE)
            connection.execute(query)
            flask.flash('Credential was added')
            return flask.redirect(flask.url_for('boss'))

    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('addcred.html', Doctor= Doctor)

########################################################################################################################

# Phone numbers: add, update, delete

########################################################################################################################

@app.route('/addnum', methods=['GET', 'POST'])
def addnum():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor = flask.request.form.get('Doctor')
        ID= sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Doctor)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Phone_number = flask.request.form.get('Number')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(phone_numbers).filter(phone_numbers.c.doctor_id.in_([id[0][0]]),
                                              phone_numbers.c.phone_number.in_([Phone_number]))
        result = query.first()
        if result:
            flask.flash('Phone Number is already in list')
            return flask.redirect(flask.url_for('addnum'))
        if Doctor == '' or Doctor is None or Phone_number=='' or Phone_number is None :
            flask.flash('Need Doctors name and number')
            return flask.redirect(flask.url_for('addnum'))
        else:
            Phone_number=int(Phone_number)
            query = sq.insert(phone_numbers).values(doctor_id=ID, phone_number=Phone_number)
            connection.execute(query)
            flask.flash('Number was added')
            return flask.redirect(flask.url_for('boss'))

    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('addnum.html', Doctor= Doctor)


@app.route('/updatenum', methods=['GET', 'POST'])
def updatenum():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor=flask.request.form.get('Doctor')
        ID = sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Doctor)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Phone_number = flask.request.form.get('Number')
        new_num = flask.request.form.get('New Number')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(phone_numbers).filter(phone_numbers.c.doctor_id.in_([id[0][0]]),
                                              phone_numbers.c.phone_number.in_([Phone_number]))
        result = query.first()
        if not result:
            flask.flash('Phone Number is not in list')
            return flask.redirect(flask.url_for('updatenum'))
        if Doctor == '' or Doctor is None or Phone_number=='' or Phone_number is None or new_num=='' or new_num is None:
            flask.flash('Need Doctors name and number and new number')
            return flask.redirect(flask.url_for('updatenum'))
        else:
            Phone_number = int(Phone_number)
            new_num = int(new_num)
            query = sq.update(phone_numbers).values(phone_number = new_num)
            query = query.where(phone_numbers.columns.phone_number==Phone_number)
            query = query.where(phone_numbers.columns.doctor_id==ID)
            results = connection.execute(query)
            if(results):
                flask.flash('Number was updated')
                return flask.redirect(flask.url_for('boss'))
            else:
                flask.flash('Number was not updated')
                return flask.redirect(flask.url_for('updatenum'))
    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('updatenum.html', Doctor=Doctor)


@app.route('/deletenum', methods=['GET', 'POST'])
def deletenum():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Doctor = flask.request.form.get('Doctor')
        ID = sq.select([doctors.columns.doctor_id]).where(doctors.columns.doctor_name == Doctor)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Phone_number = flask.request.form.get('Number')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(phone_numbers).filter(phone_numbers.c.doctor_id.in_([id[0][0]]),
                                              phone_numbers.c.phone_number.in_([Phone_number]))
        result = query.first()
        if not result:
            flask.flash('Phone Number is not in list')
            return flask.redirect(flask.url_for('deletenum'))
        if Doctor == '' or Doctor is None or Phone_number == '' or Phone_number is None:
            flask.flash('Need Doctors name and number and new number')
            return flask.redirect(flask.url_for('updatenum'))
        else:
            Phone_number = int(Phone_number)
            query = sq.delete(phone_numbers).where(phone_numbers.c.phone_number == Phone_number)
            query=query.where(phone_numbers.columns.doctor_id==ID)
            results = connection.execute(query)
            if (results):
                flask.flash('Number was deleted')
                return flask.redirect(flask.url_for('boss'))
            else:
                flask.flash('Number was not deleted')
                return flask.redirect(flask.url_for('deletenum'))
    doc = sq.select([doctors.columns.doctor_name])
    ResultProxy = connection.execute(doc)
    Doctor = ResultProxy.fetchall()
    return flask.render_template('deletenum.html', Doctor=Doctor)


########################################################################################################################

# Inpatient (Hospital_ID (FK), Inpatient Medical Procedure name, cost of procedure, cost of stay per night)

########################################################################################################################

@app.route('/addin', methods=['GET', 'POST'])
def addin():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('Name')
        Cost = flask.request.form.get('Cost')
        Night = flask.request.form.get('Night')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(inpatients).filter(inpatients.c.hospital_id.in_([id[0][0]]),
                                           inpatients.c.inpatient_procedure_name.in_([Name]))
        result = query.first()
        if result:
            flask.flash('This procedure already exists')
            return flask.redirect(flask.url_for('addin'))
        if Hospital == '' or Hospital is None or Name=='' or Name is None or Cost=='' or Cost is None:
            flask.flash('Need Hospital, Procedure Name and Cost')
            return flask.redirect(flask.url_for('addin'))


        if Night!='':
            Cost=float(Cost)
            Night=float(Night)
            query = sq.insert(inpatients).values(hospital_id=ID, inpatient_procedure_name=Name,
                                                     cost_of_procedure=Cost, cost_of_stay_per_night=Night )
            connection.execute(query)
            flask.flash('Inpatient Information was added')
            return flask.redirect(flask.url_for('boss'))
        else:
            Cost = float(Cost)

            query = sq.insert(inpatients).values(hospital_id=ID, inpatient_procedure_name=Name,
                                                 cost_of_procedure=Cost)
            connection.execute(query)
            flask.flash('Inpatient Information was added')
            return flask.redirect(flask.url_for('boss'))

    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    return flask.render_template('addin.html', Hospital=Hospital)


@app.route('/updatein', methods=['GET', 'POST'])
def updatein():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('pro')
        Night = flask.request.form.get('Night')
        new_cost = flask.request.form.get('New Cost')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(inpatients).filter(inpatients.c.hospital_id.in_([id[0][0]]),
                                           inpatients.c.inpatient_procedure_name.in_([Name]))
        result = query.first()
        if not result:
            flask.flash('This procedure does not exists')
            return flask.redirect(flask.url_for('updatein'))
        if Hospital == '' or Hospital is None or Name == '' or Name is None :
            flask.flash('Need Hospital, Procedure Name')
            return flask.redirect(flask.url_for('updatein'))
        else:
            if Night != '' and new_cost != '':
                new_cost = float(new_cost)
                Night = float(Night)

                query = sq.update(inpatients).values(cost_of_procedure=new_cost)
                query = query.values(cost_of_stay_per_night=Night)
                query = query.where(inpatients.columns.hospital_id == id[0][0])
                query = query.where(inpatients.columns.inpatient_procedure_name == Name)
                results = connection.execute(query)
                if results:
                    flask.flash('Cost per night and cost for procedure were updated')
                    return flask.redirect(flask.url_for('boss'))
                else:
                    flask.flash('Cost per night and cost for procedure were not updated')
                    return flask.redirect(flask.url_for('updatein'))
            elif Night != '':
                Night = float(Night)

                query = sq.update(inpatients).values(cost_of_stay_per_night=Night)
                query = query.where(inpatients.columns.hospital_id == id[0][0])
                query = query.where(inpatients.columns.inpatient_procedure_name == Name)
                results = connection.execute(query)
                if (results):
                    flask.flash('Cost per night was updated')
                    return flask.redirect(flask.url_for('boss'))
                else:
                    flask.flash('Cost per night was not updated')
                    return flask.redirect(flask.url_for('updatein'))

            else:
                new_cost = float(new_cost)

                query = sq.update(inpatients).values(cost_of_procedure=new_cost)
                query = query.where(inpatients.columns.hospital_id == id[0][0])
                query = query.where(inpatients.columns.inpatient_procedure_name == Name)
                results = connection.execute(query)
                if (results):
                    flask.flash('Cost per night and cost for procedure were updated')
                    return flask.redirect(flask.url_for('boss'))
                else:
                    flask.flash('Cost per night and cost for procedure were not updated')
                    return flask.redirect(flask.url_for('updatein'))

    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    procedure = sq.select([inpatients.columns.inpatient_procedure_name])
    ResultProxy = connection.execute(procedure)
    pro = ResultProxy.fetchall()

    return flask.render_template('updatein.html', Hospital=Hospital, pro=pro)



@app.route('/deletein', methods=['GET', 'POST'])
def deletein():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('pro')

        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(inpatients).filter(inpatients.c.hospital_id.in_([id[0][0]]),
                                           inpatients.c.inpatient_procedure_name.in_([Name]))
        result = query.first()
        if not result:
            flask.flash('This procedure does not exist')
            return flask.redirect(flask.url_for('deletein'))
        if Hospital == '' or Hospital is None or Name == '' or Name is None:
            flask.flash('Need Hospital, Procedure Name')
            return flask.redirect(flask.url_for('deletein'))
        else:
            query = sq.delete(inpatients).where(inpatients.columns.hospital_id == id[0][0])
            query = query.where(inpatients.columns.inpatient_procedure_name == Name)
            results = connection.execute(query)
            if results:
                flask.flash('The procedure was deleted')
                return flask.redirect(flask.url_for('boss'))
            else:
                flask.flash('The procedure was not deleted')
                return flask.redirect(flask.url_for('deletein'))
    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    procedure = sq.select([inpatients.columns.inpatient_procedure_name])
    ResultProxy = connection.execute(procedure)
    pro = ResultProxy.fetchall()

    return flask.render_template('deletein.html', Hospital=Hospital, pro=pro)



########################################################################################################################

# Outpatient ( Hospital_ID (FK), Outpatient Medical Procedure name, cost of procedure)
# R6: Doctor(Doctor_ID, name)

########################################################################################################################
@app.route('/addout', methods=['GET', 'POST'])
def addout():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('Name')
        Cost = flask.request.form.get('Cost')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(outpatients).filter(outpatients.c.hospital_id.in_([id[0][0]]),
                                            outpatients.c.outpatient_procedure_name.in_([Name]))
        result = query.first()
        if result:
            flask.flash('This procedure already exists')
            return flask.redirect(flask.url_for('addin'))
        if Hospital == '' or Hospital is None or Name == '' or Name is None or Cost == '' or Cost is None:
            flask.flash('Need Hospital, Procedure Name and Cost')
            return flask.redirect(flask.url_for('addin'))

        else:
            Cost = float(Cost)
            query = sq.insert(outpatients).values(hospital_id=id[0][0], outpatient_procedure_name=Name,
                                                 cost_of_procedure=Cost)
            connection.execute(query)
            flask.flash('Outpatient Information was added')
            return flask.redirect(flask.url_for('boss'))

    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    return flask.render_template('addout.html', Hospital=Hospital)


@app.route('/updateout', methods=['GET', 'POST'])
def updateout():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('pro')
        new_cost=flask.request.form.get('New Cost')
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(outpatients).filter(outpatients.c.hospital_id.in_([id[0][0]]),
                                            outpatients.c.outpatient_procedure_name.in_([Name]))
        result = query.first()
        if not result:
            flask.flash('This procedure does not exists')
            return flask.redirect(flask.url_for('updateout'))
        if Hospital == '' or Hospital is None or Name == '' or Name is None :
            flask.flash('Need Hospital, Procedure Name')
            return flask.redirect(flask.url_for('updateout'))
        else:

            new_cost = float(new_cost)

            query = sq.update(outpatients).values(cost_of_procedure=new_cost)
            query = query.where(outpatients.columns.hospital_id == id[0][0])
            query = query.where(outpatients.columns.outpatient_procedure_name == Name)
            results = connection.execute(query)
            if (results):
                flask.flash('Cost for procedure were updated')
                return flask.redirect(flask.url_for('boss'))
            else:
                flask.flash('Cost for procedure were not updated')
                return flask.redirect(flask.url_for('updateout'))

    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    procedure = sq.select([outpatients.columns.outpatient_procedure_name])
    ResultProxy = connection.execute(procedure)
    pro = ResultProxy.fetchall()

    return flask.render_template('updateout.html', Hospital=Hospital, pro=pro)



@app.route('/deleteout', methods=['GET', 'POST'])
def deleteout():
    if not flask.g.user:
        return flask.redirect(flask.url_for('error'))
    if flask.request.method == 'POST':
        Hospital = flask.request.form.get('Hospital')
        ID = sq.select([hospitals.columns.hospital_id]).where(hospitals.columns.hospital_name == Hospital)
        ResultProxy = connection.execute(ID)
        id = ResultProxy.fetchall()
        Name = flask.request.form.get('pro')

        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(outpatients).filter(outpatients.c.hospital_id.in_([id[0][0]]),
                                            outpatients.c.outpatient_procedure_name.in_([Name]))
        result = query.first()
        if not result:
            flask.flash('This procedure does not exist')
            return flask.redirect(flask.url_for('deleteout'))
        if Hospital == '' or Hospital is None or Name == '' or Name is None:
            flask.flash('Need Hospital, Procedure Name')
            return flask.redirect(flask.url_for('deleteout'))
        else:
            query = sq.delete(outpatients).where(outpatients.columns.hospital_id == id[0][0])
            query = query.where(outpatients.columns.outpatient_procedure_name == Name)
            results = connection.execute(query)
            if results:
                flask.flash('The procedure was deleted')
                return flask.redirect(flask.url_for('boss'))
            else:
                flask.flash('The procedure was not deleted')
                return flask.redirect(flask.url_for('deleteout'))
    hosp = sq.select([hospitals.columns.hospital_name])
    ResultProxy = connection.execute(hosp)
    Hospital = ResultProxy.fetchall()

    procedure = sq.select([outpatients.columns.outpatient_procedure_name])
    ResultProxy = connection.execute(procedure)
    pro = ResultProxy.fetchall()

    return flask.render_template('deleteout.html', Hospital=Hospital, pro=pro)


########################################################################################################################

# Security breaches

########################################################################################################################
@app.route('/error')
def error():
    return flask.render_template('BAD.html')


@app.before_request
def before_request():
    flask.g.user = None
    if 'username' in flask.session:
        flask.g.user = flask.session['username']


@app.route('/getsession')  # user is in session dic then it returns what it is, otherwise it says not logged in
def getsession():
    if 'username' in flask.session:
        return flask.session['username']
    return 'Not logged in! '


########################################################################################################################

# Logout

########################################################################################################################

@app.route('/sign_out')
def sign_out():
    flask.session.pop('username')
    return flask.redirect(flask.url_for('index'))


@app.route('/dropsession')
def dropsession():
    flask.session.pop('username', None)
    return 'Dropped'




if __name__ == '"___main___':
    app.run(debug=True)

