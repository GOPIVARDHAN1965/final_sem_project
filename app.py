import bcrypt
from flask import Flask, redirect, render_template, request, session, url_for
import pymongo

app = Flask(__name__, static_folder='static/',
            template_folder='templates', static_url_path='/static/')
app.secret_key = '!secret'

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
        user = {'fname': request.form['fname'],'lname': request.form['lname'], 'email': request.form['email'], 'pwd1': request.form['pwd1'], 'pwd2': request.form['pwd2']}
        if (user['fname']=='' or user['lname']=='' or user['email']=='' or user['pwd1']=='' or user['pwd2']==''):
            return  render_template('landing_page.html', message='All data must be filled')
        existing_user = users.find_one({'email': user['email']})
        print(existing_user)
        if existing_user == None:
            if request.form['pwd1'] == request.form['pwd2']:
                hashpass = bcrypt.hashpw(request.form['pwd1'].encode('utf-8'), bcrypt.gensalt())
                users.insert_one({'email': user['email'], 'password': hashpass,'first_name': user['fname'], 'last-name': user['lname']})
                session['user_id'] = user['email']
                return 'user registered'
            else:
                return render_template('landing_page.html', message = "Both passwords must be same!")
        print("user already exists")
        return render_template('landing_page.html', message = "user already exists")
    return render_template('landing_page.html', message='')


@app.route('/login', methods=['POST','GET'])
def login_page():
    if request.method=='POST':
        login_user = users.find_one({'email': request.form['email']})
        if login_user:
            if bcrypt.hashpw(request.form['pwd1'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['user_id'] = request.form['email']
                return "user logged in"
            return render_template(('login_page.html'), message = 'please check your password')
        return render_template(('login_page.html'), message = 'There is no account linked to this email')
    return render_template('login_page.html', message="")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing_page'))

if __name__ == "__main__":
    app.run(debug=True)
