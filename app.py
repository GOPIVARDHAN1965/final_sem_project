import bcrypt
from flask import Flask, redirect, render_template, request, session, url_for
import pymongo
# for analysis
from matplotlib.figure import Figure
import pandas as pd
import base64
from io import BytesIO


app = Flask(__name__, static_folder='static/',
            template_folder='templates', static_url_path='/static/')
app.secret_key = '!secret'
df = pd.read_csv('purchases.csv')
month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}



try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=1000
    )
    db = mongo.final_project
    mongo.server_info()
except:
    print("Error connecting to the DB")


####################################################
# db collections here
users = db.users


####################################################
# sign in page
@app.route('/', methods=['GET', 'POST'])
@app.route('/landing_page', methods=['GET', 'POST'])
def landing_page():
    if request.method == 'POST':
        user = {'fname': request.form['fname'], 'lname': request.form['lname'],
                'email': request.form['email'], 'pwd1': request.form['pwd1'], 'pwd2': request.form['pwd2']}
        if (user['fname'] == '' or user['lname'] == '' or user['email'] == '' or user['pwd1'] == '' or user['pwd2'] == ''):
            # print('Please fill the form to procced')
            return render_template('landing_page.html', message='Please fill the form to procced')
        existing_user = users.find_one({'email': user['email']})
        print(existing_user)
        if existing_user == None:
            if request.form['pwd1'] == request.form['pwd2']:
                hashpass = bcrypt.hashpw(
                    request.form['pwd1'].encode('utf-8'), bcrypt.gensalt())
                users.insert_one({'email': user['email'], 'password': hashpass,
                                 'first_name': user['fname'], 'last-name': user['lname']})
                session['user_id'] = user['email']
                return redirect(url_for('home'))
            else:
                return render_template('landing_page.html', message="Both passwords must be same!")
        print("user already exists")
        return render_template('landing_page.html', message="user already exists")
    return render_template('landing_page.html', message='')

####################################################
# login in page


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if request.method == 'POST':
        login_user = users.find_one({'email': request.form['email']})
        if login_user:
            if bcrypt.hashpw(request.form['pwd1'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['user_id'] = request.form['email']
                return redirect(url_for('home'))
            return render_template(('login_page.html'), message='please check your password')
        return render_template(('login_page.html'), message='There is no account linked to this email')
    return render_template('login_page.html', message="")


####################################################
# home page per year
@app.route('/home', methods=['GET'])
def home():
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        print(user)
        print(session)
        return render_template('home.html', user=user)
    return redirect(url_for('login_page'))


####################################################
# Dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' in session:
        print('user in session')
        user = users.find_one({'email': session['user_id']})
        fig = Figure(figsize=(12, 8), linewidth=0)
        ax = fig.subplots()
        single_customer = df[df['CustomerID'] == user['CustomerID']]
        # single_customer = df[df['CustomerID'] == 17914]
        #monthly spend
        month = single_customer.groupby('Month')['TotalPrice'].sum()
        ax.bar(month.index, month,)
        ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
        ax.set_xlabel('Months')
        ax.set_ylabel('Amount spent')
        ax.set_title('My yearly expense')
        print(sum(month))
        print(month.index)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        print(month.to_dict())
        return render_template('dashboard.html', year=data, user=user, month_names = month_names, months_data = month.to_dict())
    return redirect(url_for('login_page'))




####################################################
# Dashboard page per month
@app.route('/<specific_month>', methods=['GET', 'POST'])
def dashboard_month(specific_month):
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        fig = Figure(figsize=(12, 8), linewidth=0)
        ax = fig.subplots()
        single_customer = df[df['CustomerID'] == user['CustomerID']]
        # single_customer = df[df['CustomerID'] == 17914]
        #monthly spend
        month = single_customer.groupby('Month')['TotalPrice'].sum()
        ax.bar(month.index, month,)
        ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
        ax.set_xlabel('Months')
        ax.set_ylabel('Amount spent')
        ax.set_title('My yearly expense')
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        #month wise
        single_month = single_customer[single_customer['Month']==int(specific_month)]
        one_month = single_month.groupby('Date')['TotalPrice'].sum() 
        fig1 = Figure(figsize=(12, 8), linewidth=0)
        axs = fig1.subplots()
        axs.bar(one_month.index, one_month,)
        # ax.set_xticks()
        axs.set_xlabel('Days')
        axs.set_ylabel('Amount spent')
        axs.set_title('My Monthly expense')
        # Save it to a temporary buffer.
        buf1 = BytesIO()
        fig1.savefig(buf1, format="png")
        buf1.seek(0)
        # Embed the result in the html output.
        data1 = base64.b64encode(buf1.getbuffer()).decode("ascii")
        print(one_month)
        return render_template('dashboard.html', year=data, month=data1, user=user,months_data = month.to_dict(), days_purchased = one_month.to_dict(), month_names = month_names)
    return redirect(url_for('login_page'))




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing_page'))


if __name__ == "__main__":
    app.run(debug=True)
