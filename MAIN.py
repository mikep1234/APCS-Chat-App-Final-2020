from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO
import sqlite3
import datetime as d

Website = Flask("localhost")

SOCKET = SocketIO(Website)

LIVE_CLIENTS = {}

#conn = sqlite3.connect("ACCOUNTS.db")

#conn.execute("DROP TABLE History")

#conn.execute("CREATE TABLE IF NOT EXISTS History(name text, sender text, messages text)")

#conn.execute("CREATE TABLE IF NOT EXISTS Friends(name text, friends text)")

#conn.execute("DELETE FROM Accounts")

#conn.execute("INSERT INTO Accounts VALUES(\"ADMIN\", \"Stella12\")")

#conn.execute("INSERT INTO Accounts VALUES(\"ADMIN2\", \"Stella12\")")

#conn.execute("DELETE FROM History")

#conn.execute("DELETE FROM Friends")

#conn.commit()

#conn.close()

@Website.route("/", methods = ["POST", "GET"])

def home():

    return render_template("Login.html")

@Website.route("/user/<name>")

def load_app(name):

    conn = sqlite3.connect("ACCOUNTS.db")

    try:

        friends_list = conn.execute("SELECT * FROM Friends WHERE name = " + "\'" + str(name) + "\'").fetchall()[0][1]

    except Exception as e:

        friends_list = ""

    conn.close()

    return render_template("ChatAppFrame.html", name = name, friends = friends_list)

@SOCKET.on('Log_In')

def log_in(data):

    conn = sqlite3.connect("ACCOUNTS.db")

    DATA = conn.execute("SELECT * FROM Accounts WHERE name = " + "\'" + data['Username'] + "\'").fetchall()

    if len(DATA) == 0:

        SOCKET.emit('failed_login', {'notice': "Failed Login! No such account exists!"}, room=request.sid)

    elif(data['Password'] == DATA[0][1]):

        SOCKET.emit('redirect', {'url': url_for('load_app', name = data['Username'])}, room=request.sid)

    else:

        SOCKET.emit('failed_login', {'notice': "Failed Login! Incorrect Password or Username!"}, room=request.sid)

@SOCKET.on('disconnect')

def disconnect():

    for item in LIVE_CLIENTS.items():

        if item[1] == request.sid:

            del LIVE_CLIENTS[item[0]]

@SOCKET.on('sign_up')

def sign_up(data):

    conn = sqlite3.connect("ACCOUNTS.db")

    temp_list = conn.execute("SELECT * FROM Accounts WHERE name = " + "\'" + str(data['account_name']) + "\'").fetchall()

    if len(temp_list) == 0 and len(str(data['password'])) >= 8:

        conn.execute("INSERT INTO Accounts VALUES(" + "\'" + data['account_name'] + "\'," + "\'" + data['password'] + "\'")

        SOCKET.emit('redirect', {'url': url_for('load_app', name = data['account_name'])}, room=request.sid)

    else:

        SOCKET.emit('failed_login', {'notice': "Failed Account Creation! Invalid password (less than 8 characters) or taken username!"}, room=request.sid)

@SOCKET.on('re_auth')

def re_auth(data):

    LIVE_CLIENTS[str(data)] = request.sid

@SOCKET.on('send_private_message')

def send_private_message(data):

    Date = str(d.datetime.now())

    conn = sqlite3.connect("ACCOUNTS.db")

    for user in LIVE_CLIENTS:

        if user == data['target'] and LIVE_CLIENTS[user] != request.sid:

            SOCKET.emit('new_private_message', {'time': data['time'], 'message': data['message'], 'sender': data['sender']}, room = LIVE_CLIENTS[user])

        if LIVE_CLIENTS[user] == request.sid:

            SOCKET.emit('new_private_message', {'time': data['time'], 'message': data['message'], 'sender': data['sender']}, room=LIVE_CLIENTS[user])

@SOCKET.on('set_history')

def set_history(data):

    conn = sqlite3.connect("ACCOUNTS.db")

    #print(conn.execute("SELECT * FROM History WHERE name = " + "\'" + data['name'] + "\'" + " and  sender = " + "\'" + data['sender'] + "\'").fetchall())

    conn.execute("DELETE FROM History WHERE name = " + "\'" + data['name'] + "\'" + " and  sender = " + "\'" + data['sender'] + "\'")

    conn.commit()

    name = "\'" + str(data['name']) + "\'"

    sender = "\'" + str(data['sender']) + "\'"

    DATA = "\"" + str(data['DATA']) + "\""

    conn.execute("INSERT INTO History VALUES(%s, %s, %s)" % (str(name), str(sender), DATA))

    conn.commit()

    conn.close()

@SOCKET.on('get_history')

def get_history(data):

    conn = sqlite3.connect("ACCOUNTS.db")

    try:

        temp_data = conn.execute("SELECT * FROM History WHERE name = %s and sender = %s;" % ("\'" + str(data['name']) + "\'", "\'" + str(data['sender']) + "\'")).fetchall()

        SOCKET.emit('get_history', {'data': temp_data[0][2]}, room = request.sid)

    except Exception as e:

        print("No History")

    conn.close()

@SOCKET.on('add_friend')

def add_friend(data):

    conn = sqlite3.connect("ACCOUNTS.db")

    temp = conn.execute("SELECT * FROM Friends WHERE name = %s" %("\'" + str(data['name']) + "\'")).fetchall()

    conn.execute("DELETE FROM Friends WHERE name = %s" %("\'" + str(data['name']) + "\'"))

    try:

        print("INSERT INTO Friends VALUES(%s, %s)" % ("\'" + str(data['name']) + "\'", "\'" + str(temp[0][1][0: -1]) + ", " + data['target'] + "]" + "\'"))

        conn.execute("INSERT INTO Friends VALUES(%s, %s)" % ("\'" + str(data['name']) + "\'", "\'" + str(temp[0][1][0: -1]) + ", " + data['target'] + "]" + "\'"))

    except Exception as e:

        print(e)

        conn.execute("INSERT INTO Friends VALUES(%s, %s)" % ("\'" + str(data['name']) + "\'", "\'" + str("[" + data['target'] + "]") + "\'"))

    conn.commit()

    conn.close()

SOCKET.run(Website)