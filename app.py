
import mysql.connector
from flask import Flask, render_template, url_for, request, redirect, flash, session

app=Flask(__name__)
app.secret_key = 'mysecretkey123'

db = mysql.connector.connect(
    host='database-2.cvoqfr3fpxww.ap-south-1.rds.amazonaws.com',
    user='admin',
    password='awsuser123',
    database='vimal'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        con = db.cursor()
        con.execute("SELECT * FROM Company WHERE username=%s AND password=%s", (username, password))
        res = con.fetchone()

        if res:
            session["username"] = res[1]
            session["password"] = res[4]
            session["user_id"] = res[0]
            return redirect("Dashboard")
        else:
            flash("Invalid Username or Password","danger")
    return redirect(url_for("index"))

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=='POST':
        try:
            company_name = request.form['company_name']
            username = request.form['username']
            password = request.form['password']
            cash = request.form['cash']
            con = db.cursor()
            con.execute("insert into Company(company_name,username,password,cash_balance)values(%s,%s,%s)",(company_name, username, password,cash))
            db.commit()
            flash("Registered Successfully")
        except:
            flash("Error in insert operation","danger")
        finally:
            return redirect(url_for("index"))
            con.close()

    return render_template('register.html')


@app.route('/Dashboard')
def Dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        con = db.cursor()


        con.execute("SELECT company_name, cash_balance FROM Company WHERE user_id = %s", (user_id,))
        company_data = con.fetchone()


        con.execute("SELECT * FROM Item WHERE user_id = %s", (user_id,))
        item_data = con.fetchall()

        con.close()

        return render_template("Dashboard.html", company_data=company_data, datas=item_data)
    else:
        return redirect(url_for("index"))


#add items
@app.route("/addItem", methods=['GET', 'POST'])
def addItem():
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        user_id = session["user_id"]
        con = db.cursor()


        con.execute("SELECT * FROM Item WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        existing_item = con.fetchone()

        if existing_item:
            con.close()
            flash("Item name already exists for this user. Choose a different name.", "error")
            return redirect(url_for("addItem"))


        sql = "INSERT INTO Item (user_id, item_name) VALUES (%s, %s)"
        try:
            con.execute(sql, (user_id, item_name))
            db.commit()
            con.close()
            return redirect(url_for("Dashboard"))
        except mysql.connector.errors.IntegrityError:
            con.close()
            flash("Error in insert operation", "danger")
            return redirect(url_for("addItem"))

    return render_template("addItem.html")



# Add Purchase
@app.route('/purchase/<string:item_name>', methods=['GET', 'POST'])
def purchase(item_name):
    con = db.cursor()
    user_id = session["user_id"]
    if request.method == 'POST':
        qty = request.form.get('qty')
        rate = request.form.get('cost')


        con.execute("SELECT cash_balance FROM Company WHERE user_id = %s ", [user_id])
        cash_balance = con.fetchone()[0]


        total_cost = int(qty) * int(rate)

        if cash_balance < total_cost:
            flash("Insufficient balance to purchase.", "error")
            con.close()
            return redirect(url_for("Dashboard"))
        else:
            con.execute("UPDATE Company SET cash_balance = cash_balance - %s", [total_cost])
            con.execute("UPDATE Item SET qty = qty + %s WHERE item_name = %s", [qty, item_name])
            con.execute("INSERT INTO Purchase (item_name, qty, rate, amount) VALUES (%s, %s, %s, %s)",[item_name, qty, rate, total_cost])
            db.commit()
            db.commit()

            con.close()
            return redirect(url_for("Dashboard"))

    sql = "select * from Item where item_name=%s "
    con.execute(sql, [item_name])
    res = con.fetchone()
    return render_template("purchase.html",datas=res)




#sell
@app.route('/sell/<string:item_name>', methods=['GET', 'POST'])
def sell(item_name):
    con = db.cursor()
    user_id = session["user_id"]
    if request.method == 'POST':
        qty = request.form.get('qty')
        rate = request.form.get('cost')

        con.execute("SELECT * FROM Item WHERE item_name = %s ", [item_name])
        res = con.fetchone()

        total_cost = int(qty) * int(rate)

        if res[2] < int(qty):
            flash("Insufficient balance to purchase.", "error")
            con.close()
            return redirect(url_for("Dashboard"))
        else:
            con.execute("UPDATE Company SET cash_balance = cash_balance + %s", [total_cost])
            con.execute("UPDATE Item SET qty = qty - %s WHERE item_name = %s", [qty, item_name])

            con.execute("INSERT INTO Sales (item_name, qty, rate, amount) VALUES (%s, %s, %s, %s)",[item_name, qty, rate, total_cost])
            db.commit()
            db.commit()
            con.close()
            return redirect(url_for("Dashboard"))

    sql = "select * from Item where item_name=%s "
    con.execute(sql, [item_name])
    res = con.fetchone()
    return render_template("sell.html",datas=res)

@app.route('/purchase_history')
def purchase_history():
    username = session["username"]
    con = db.cursor()
    con.execute("SELECT company_name, cash_balance FROM Company WHERE username  = %s", [username])
    company_data = con.fetchone()
    con.execute("SELECT * FROM Purchase" )
    purchase_history = con.fetchall()
    con.close()
    return render_template("purchase_history.html", purchase_history=purchase_history, company_data=company_data)

@app.route('/sell_history')
def sell_history():
    username = session["username"]
    con = db.cursor()
    con.execute("SELECT company_name, cash_balance FROM Company WHERE username  = %s", [username])
    company_data = con.fetchone()
    con.execute("SELECT * FROM Sales" )
    sell_history = con.fetchall()
    con.close()
    return render_template("sell_history.html", sell_history=sell_history, company_data=company_data)

@app.route('/delete_item/<string:item_name>', methods=['POST'])
def delete_item(item_name):
    if "user_id" in session:
        user_id = session["user_id"]
        con = db.cursor()
        con.execute("DELETE FROM Item WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        db.commit()
        con.close()
    return redirect(url_for('Dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))


if(__name__=='__main__'):
    app.run(debug=True)
