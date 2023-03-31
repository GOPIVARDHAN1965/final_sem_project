import bcrypt
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
import pymongo
# for analysis
from matplotlib.figure import Figure
import pandas as pd
import base64
from io import BytesIO
import random

app = Flask(__name__, static_folder='static/',
            template_folder='templates', static_url_path='/static/')
app.secret_key = '!secret'
df = pd.read_csv('purchases.csv')
df['TotalPrice'] = df['TotalPrice'].round(decimals=2)
df['Year'] = pd.to_datetime(df['Date']).dt.year
items = pd.read_excel('items_list.xlsx')
items['Description'] = items['Description'].astype(str)
month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
ndf = df.pivot_table(index='StockCode', columns='InvoiceNo', values='Quantity')
ndf.fillna(0, inplace=True)
from scipy.sparse import csr_matrix
csr_data = csr_matrix(ndf.values)
ndf.reset_index(inplace=True)
# ndf
from sklearn.neighbors import NearestNeighbors
knn=NearestNeighbors(metric='cosine',n_neighbors=10)
knn.fit(csr_data)


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
                custId = random.choice(df['CustomerID'].unique())
                print(users.find_one({'CustomerID':int(str(custId)) }))
                while users.find_one({'CustomerID':int(str(custId)) })!=None:
                    custId = random.choice(df['CustomerID'].unique())
                custId = int(str(custId))
                users.insert_one({'email': user['email'], 'password': hashpass,'first_name': user['fname'], 'last-name': user['lname'],'CustomerID': custId})
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
# home page 
@app.route('/home', methods=['GET'])
def home():
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        # print(user)
        # print(session)
        # the top ten items purchased by the customer
        top_purchses = df[df['CustomerID']==user['CustomerID']].groupby('StockCode')['Quantity'].sum().sort_values(ascending=False).index[:10].to_list()
        recommendations = set()
        for each_item in top_purchses:
            ndf[ndf['StockCode'] == each_item].index[0]
            similarities,indeces=knn.kneighbors(csr_data[ndf[ndf['StockCode'] == each_item].index[0]],n_neighbors=5)
            rec = sorted(zip(indeces.squeeze().tolist(),similarities.squeeze().tolist()),key=lambda x:x[1])[:0:-1]
            # print('Recommendations for item '+df[df['StockCode']==each_item]['Description'].values[0]+ 'are : ')
            for val in rec:
                recommendations.add(ndf.iloc[val[0]]['StockCode'])
        # print(recommendations)
        item_data = []
        for each_code in recommendations:
            temp = items[items['StockCode']==each_code].iloc[0]
            item_data.append({'StockCode':temp['StockCode'],'Description' :temp['Description'],'UnitPrice': temp['UnitPrice'],'img': temp['img']})
        # print(item_data)
        #top picks by users around you
        top_picks=df.groupby(['StockCode'])['Quantity'].sum().sort_values(ascending=False)
        top_picks=top_picks[:30].index.to_list()
        top_data = []
        for each_code in top_picks:
            temp = items[items['StockCode']==each_code].iloc[0]
            top_data.append({'StockCode':temp['StockCode'],'Description' :temp['Description'],'UnitPrice': temp['UnitPrice'],'img': temp['img']})
        # print(top_data)
        return render_template('home.html', user=user, item_data = item_data, top_data=top_data)
    return redirect(url_for('login_page'))


####################################################
# search bar
@app.route('/search')
def search():
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        query = request.args['box-txt']
        # print(query)
        # print(type(query))
        result = items.loc[items['Description'].str.contains(query.upper())]['Description']
        suggestions = result.to_list()
        # print(suggestions[:10])
        # return jsonify(suggestions[:10])
        return render_template('search.html', user=user,suggestions=suggestions[:12],query=query)
    return redirect(url_for('login_page'))


####################################################
# search bar
@app.route('/home/<name>')
def find_item(name):
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        top_purchses = df.loc[df['Description'].str.contains(name.upper()),]['StockCode'].to_list()[0]
        recommendations = set()
        ndf[ndf['StockCode'] == top_purchses].index[0]
        similarities,indeces=knn.kneighbors(csr_data[ndf[ndf['StockCode'] == top_purchses].index[0]],n_neighbors=10)
        rec = sorted(zip(indeces.squeeze().tolist(),similarities.squeeze().tolist()),key=lambda x:x[1])[:0:-1]
        # print('Recommendations for item '+df[df['StockCode']==each_item]['Description'].values[0]+ 'are : ')
        for val in rec:
            recommendations.add(ndf.iloc[val[0]]['StockCode'])
        # print(recommendations)
        item_data = []
        temp = items[items['StockCode']==top_purchses].iloc[0]
        item_data.append({'StockCode':temp['StockCode'],'Description' :temp['Description'],'UnitPrice': temp['UnitPrice'],'img': temp['img']})
        # print(item_data)
        for each_code in recommendations:
            temp = items[items['StockCode']==each_code].iloc[0]
            item_data.append({'StockCode':temp['StockCode'],'Description' :temp['Description'],'UnitPrice': temp['UnitPrice'],'img': temp['img']})
        # print(item_data)
        return render_template('find_item.html', user=user, item_data = item_data)
    return redirect(url_for('login_page'))


####################################################
# Dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' in session:
        # print('user in session')
        user = users.find_one({'email': session['user_id']})
        years_available = df[df['CustomerID']==user['CustomerID']]['Year'].unique()
        # print(years_available)
        fig = Figure(figsize=(12, 8), linewidth=0)
        ax = fig.subplots()
        single_customer = df[(df['CustomerID'] == user['CustomerID']) & (df['Year']==years_available[0])]
        # single_customer = df[df['CustomerID'] == 17914]
        #monthly spend
        month = single_customer.groupby('Month')['TotalPrice'].sum()
        ax.bar(month.index, month,)
        ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
        ax.set_xlabel('Months')
        ax.set_ylabel('Amount spent')
        ax.set_title('My yearly expense')
        # print(sum(month))
        # print(month.index)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        month=month.to_dict()
        for i in month:
            month[i] = round(month[i],3)
            # print(month[i])
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        # print(month.to_dict())
        return render_template('dashboard.html', year=data, user=user, month_names = month_names, months_data = month,years_available=years_available)
    return redirect(url_for('login_page'))


####################################################
# Dashboard page
@app.route('/dashboard/<year>', methods=['GET', 'POST'])
def dashboard_year(year):
    if 'user_id' in session:
        # print('user in session')
        user = users.find_one({'email': session['user_id']})
        years_available = df[df['CustomerID']==user['CustomerID']]['Year'].unique()
        # print(years_available)
        fig = Figure(figsize=(12, 8), linewidth=0)
        ax = fig.subplots()
        single_customer = df[(df['CustomerID'] == user['CustomerID']) & (df['Year']==int(year))]
        # single_customer = df[df['CustomerID'] == 17914]
        #monthly spend
        month = single_customer.groupby('Month')['TotalPrice'].sum()
        # print(month)
        ax.bar(month.index, month,)
        ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
        ax.set_xlabel('Months')
        ax.set_ylabel('Amount spent')
        ax.set_title('My yearly expense')
        # print(sum(month))
        # print(month.index)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        month=month.to_dict()
        for i in month:
            month[i] = round(month[i],3)
        month['year'] = int(year)
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        # print(month.to_dict())
        return render_template('dashboard.html', year=data, user=user, month_names = month_names, months_data = month,years_available=years_available)
    return redirect(url_for('login_page'))




####################################################
# Dashboard page per month
@app.route('/dashboard/<year>/<specific_month>', methods=['GET', 'POST'])
def dashboard_month(year,specific_month):
    if 'user_id' in session:
         # print('user in session')
        user = users.find_one({'email': session['user_id']})
        years_available = df[df['CustomerID']==user['CustomerID']]['Year'].unique()
        # print(years_available)
        fig = Figure(figsize=(12, 8), linewidth=0)
        ax = fig.subplots()
        single_customer = df[(df['CustomerID'] == user['CustomerID']) & (df['Year']==int(year))]
        # single_customer = df[df['CustomerID'] == 17914]
        #monthly spend
        month = single_customer.groupby('Month')['TotalPrice'].sum()
        # print(month)
        ax.bar(month.index, month,)
        ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
        ax.set_xlabel('Months')
        ax.set_ylabel('Amount spent')
        ax.set_title('My yearly expense')
        # print(sum(month))
        # print(month.index)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        month=month.to_dict()
        for i in month:
            month[i] = round(month[i],3)
        month['year'] = int(year)
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
        one_month = one_month.to_dict()
        for i in one_month:
            one_month[i] = round(one_month[i],3)
        # Embed the result in the html output.
        data1 = base64.b64encode(buf1.getbuffer()).decode("ascii")
        # print(one_month)
        return render_template('dashboard.html', year=data, month=data1, user=user,months_data = month, days_purchased = one_month, month_names = month_names,years_available=years_available)
    return redirect(url_for('login_page'))


####################################################
# View invoice per each date
@app.route('/invoice/<date>')
def invoice(date):
    if 'user_id' in session:
        print(date[:4])
        user = users.find_one({'email': session['user_id']})
        invoice_df = df[(df['CustomerID']==user['CustomerID']) & (df['Date']==date)]
        invoices = invoice_df['InvoiceNo'].unique()
        return render_template('invoice.html',user=user, invoices = invoices ,date=date)
    

####################################################
# View invoice per each date
@app.route('/view-invoice/<invoice>')
def view_invoice(invoice):
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        invoice_data = df[(df['CustomerID']==user['CustomerID']) & (df['InvoiceNo']==int(invoice))]
        ninvoice_data = invoice_data.to_dict(orient = 'records')
        total = invoice_data.groupby('InvoiceNo')['TotalPrice'].sum()
        total= (total.values)
        total = total[0]
        return render_template('view_invoice.html',user=user,data=ninvoice_data, total=round(total,2))


####################################################
# profile update
@app.route('/profile')
def profile():
    if 'user_id' in session:
        user = users.find_one({'email': session['user_id']})
        return render_template('profile.html',user=user,)


####################################################
# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing_page'))


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=8010)
    # app.run(debug=True)