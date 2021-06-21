from flask import Flask, render_template, json, request, url_for, session, redirect, make_response
from datetime import timedelta
import hashlib
import pymongo
from bson.objectid import ObjectId 

import os
import sys

app = Flask(__name__)
app.config.from_pyfile('settings.conf')
app.secret_key = app.config['SECRET_KEY']

client = pymongo.MongoClient(app.config['DATABASE']['host'], app.config['DATABASE']['port'])
db = client[app.config['DATABASE']['db']]

@app.before_request
def make_session_permanent():
	session.permanent = True
	app.permanent_session_lifetime = timedelta(minutes=30)

@app.route('/', methods=['GET','POST'])
def index():
	return render_template('maypp_main.html', error = 0)

@app.route('/my', methods=['GET','POST'])
def my():
	if 'username' in session:
		answers_collection = db[session['username']]
		userprofile = db['users'].find({'username': session['username']})[0]
		return render_template('maypp_start.html', username=session['username'], userprofile = userprofile, answers = answers_collection.find())
	return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		login = request.form['login']
		passw = hashlib.sha1(request.form['password'].encode('utf-8'))
		if login in app.config['USERS']:
			if passw.hexdigest() == app.config['USERS'][login]:
				session['username'] = login
				return redirect(url_for('my'))
			else:
				return render_template('maypp_main.html', error = 1)
		else:
			return render_template('maypp_main.html', error = 1)
	else:
		return redirect(url_for('index'))

@app.route("/answers/<answer_id>/delete", methods=['POST'])
def answerDelete(answer_id):
	db[session['username']].remove({"_id": ObjectId(answer_id)})
	return redirect(url_for('my'))

@app.route("/addNewAnswer", methods=['POST'])
def answerAdd():
	newAns = { 
		"name": request.form["nameAnswer"],
		"text": request.form["textAnswer"],
		"categories": request.form["metawordAnswer"],
		"keyword": request.form["keywordAnswer"].split(', '),
	}
	db[session['username']].insert(newAns)
	return redirect(url_for('my'))

@app.route("/editAnswer/<answer_id>/edit", methods=['POST'])
def answerEdit(answer_id):
	editAns = { 
		"name": request.form["nameAnswer"],
		"text": request.form["textAnswer"],
		"categories": request.form["metawordAnswer"],
		"keyword": request.form["keywordAnswer"].split(', '),
	}
	db[session['username']].update({"_id": ObjectId(answer_id)}, editAns)
	return redirect(url_for('my'))

@app.route("/editSettings", methods=['POST'])
def settingsEdit():
	editSet = { 
		"username": session['username'],
		"status": request.form['radio'],
		"vk_token": request.form["vk-token"],
		"id_group": request.form["id-group"],
	}
	db['users'].update({'username': session['username']}, editSet)
	return redirect(url_for('my'))

@app.route('/logout', methods=['GET','POST'])
def logout():
	session.pop('username', False)
	return redirect(url_for('index'))

# вот тут лучше бы, конечно, мне изначально создать класс бота в файле mybot.py и уже здесь объявлять объект именем пользователя при запуске бота, но я не ищу легких путей :( Прошляпила, каюсь...
@app.route('/start', methods=['POST'])
def startapp():
	command = 'python3 mybot.py ' + session['username']
	os.system(command)
	return render_template('error_bot.html')

@app.route('/stop', methods=['POST'])
def stopapp():
	command = 'pkill -f mybot.py'
	os.system(command)
	return redirect(url_for('my')) 

if __name__ == '__main__':
    app.run()
