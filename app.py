from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods = ['GET','POST'])
@app.route('/landing_page', methods = ['GET','POST'])
def landing_page():
    if request.method == 'POST':
        user = {'fname': request.form['fname'], 'lname': request.form['lname'], 'email': request.form['email']  }
        print(user)
        return render_template('landing_page.html')
    
    return render_template('landing_page.html')




if __name__ == "__main__":
    app.run(debug=True)
