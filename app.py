from flask import Flask, render_template, request
import pymongo

app = Flask(__name__, static_folder='static/', template_folder='templates', static_url_path='/static/')
app.secret_key = '!secret'

try:
    mongo = pymongo.MongoClient(
        host = "localhost",
        port = 27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.final_project
    mongo.server_info()
except:
    print("Error connecting to the DB")


####################################################
#db collections here 
users = db.users






@app.route('/', methods = ['GET','POST'])
@app.route('/landing_page', methods = ['GET','POST'])
def landing_page():
    if request.method == 'POST':
        user = {'fname': request.form['fname'], 'lname': request.form['lname'], 'email': request.form['email']}
        users.insert_one(user)
        print(user)
        return render_template('landing_page.html')
    
    return render_template('landing_page.html')

if __name__ == "__main__":
    app.run(debug=True)
