

from flask import Flask, render_template
from matplotlib.figure import Figure
import pandas as pd
import base64
from io import BytesIO



app = Flask(__name__)

df = pd.read_csv('purchases.csv')




@app.route("/")
def hello():
    # Generate the figure **without using pyplot**.
    fig = Figure(figsize=(8,4),facecolor='#f0f0f0',linewidth=0)
    ax = fig.subplots()
    single_customer = df[df['CustomerID']==17841]
    # ax.plot([1, 2,3],[])
    month=single_customer.groupby('Month')['TotalPrice'].sum()
    ax.bar(month.index, month,)
    ax.set_xticks(month.index)

    # ax.set_xlabel('X-axis')
    # ax.set_ylabel('Y-axis')
    ax.set_title('My yearly expense')
    # Save it to a temporary buffer. 
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return render_template('dashboard.html', data=data)
    return f"<img src='data:image/png;base64,{data}'/>"

if __name__ == '__main__':
    app.run(debug=True)
 