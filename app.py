import sqlite3 as sql

import datetime
import time
import timeago
from flask import Flask, session, render_template, request, redirect

app = Flask(__name__, static_url_path='/static')
app.debug = True
app.secret_key = 'this_is_so_secret'

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'logged_in' not in session:
        msg = []
        error = False
        logged_in = False
        if request.method == 'POST':
            with sql.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("select * from accounts where username=? and password=?",
                            (str(request.form['username']),
                             str(request.form['password'])))

                row = cur.fetchone()
                if row is None:
                    msg.append('Username or password is incorrect!')
                    error = True
                else:
                    msg.append('Logged in successfully!')
                    session['logged_in'] = True
                    session['username'] = str(request.form['username'])
                    session['user_id'] = str(row[0])
                    logged_in = True

                return render_template('pages/login.html', title="Login", message=msg, error=error, login=logged_in)
        if request.method == 'GET':
            return render_template('pages/login.html', title="Login")
    else:
        return redirect("/")


@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'logged_in' not in session:
        msg = []
        error = False
        registered = False

        with sql.connect("database.db") as con1:
            groups = con1.cursor()
            groups.execute('select * from groups')
            all_groups = groups.fetchall()

        if request.method == 'POST':
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute("select * from accounts where username=?", (str(request.form['username']),))
            username_exists = cursor.fetchall()

            try:
                if str(request.form['password']) != str(request.form['password-repeat']):
                    msg.append("Passwords are not the same!")
                    error = True

                datem = datetime.datetime.strptime(request.form['birthday'], "%Y-%m-%d")

                if datetime.datetime.today().year - datem.year <= 18:
                    msg.append("You are younger than 18!")
                    error = True

                if username_exists:
                    msg.append("Username exists!")
                    error = True

                if not error:
                    with sql.connect("database.db") as con:
                        cur = con.cursor()
                        cur.execute(
                            "INSERT INTO accounts (fullname, username, email, password, register_ip, birthday, create_date, school_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                            (request.form['fullname'], request.form['username'], request.form['email'],
                             str(request.form['password']), str(request.remote_addr), str(request.form['birthday']),
                             str(time.time()), int(request.form['school'])))
                        con.commit()
                        msg.append("Account created successfully!")
                        registered = True
            except:
                con.rollback()
                msg.append("Error in insert operation!")
                error = True
            finally:
                return render_template("pages/register.html", title="Register", message=msg, error=error,
                                       registered=registered, groups=all_groups)
        if request.method == 'GET':
            return render_template("pages/register.html", title="Register", groups=all_groups)
    else:
        return redirect("/")


@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from posts')
        posts = cursor.fetchall()

        all = []
        for post in posts:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from accounts where id=?', (post[4],))
            account = cursor.fetchone()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=?', (int(post[0]),))
            likes = cursor.fetchall()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=? and user_id=?',
                               (int(post[0]), int(session['user_id']),))
            is_liked = cursor.fetchall()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from groups where id=?', (post[6],))
            group = cursor.fetchone()

            all.append(
                {'id': post[0], 'username': account[2], 'title': post[1],
                 'create_date': timeago.format(datetime.datetime.fromtimestamp(float(post[2])),
                                               datetime.datetime.now()), 'content': post[3],
                 'url_key': post[5], 'group': group[2], 'total_likes': str(len(likes)), 'is_liked': bool(is_liked)})

        return render_template('pages/index.html', title="Homepage", username=session['username'],
                               posts=all)


@app.route('/profile', methods=['POST', 'GET'])
def profile():
    global username_exists
    msg = []
    error = False
    updated = False

    if 'logged_in' not in session:
        return redirect("/login")
    else:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("select * from accounts where username=?", (str(session['username']),))

        account_data = cur.fetchall()[0]

        if request.method == 'POST':
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute("select * from accounts where username=?", (str(request.form['username']),))
            username_exists = cursor.fetchall()

            try:
                datem = datetime.datetime.strptime(request.form['birthday'], "%Y-%m-%d")

                if datetime.datetime.today().year - datem.year <= 18:
                    msg.append("Age should be above 18!")
                    error = True

                if request.form['current-password'] != account_data[4]:
                    msg.append("Password is incorrect!")
                    error = True

                if username_exists:
                    msg.append("Username exists!")
                    error = True

                if not error:
                    with sql.connect("database.db") as con:
                        cur = con.cursor()
                        cur.execute(
                            "UPDATE accounts SET fullname=?, birthday=?, email=?, username=?, password=? WHERE id = ?",
                            (str(request.form['fullname']), str(request.form['birthday']), str(request.form['email']),
                             str(request.form['username']),
                             str(request.form['new-password']) or account_data[4],
                             str(account_data[0])))
                        con.commit()
                        msg.append("Updated account successfully!")
                        updated = True
                        session['username'] = str(request.form['username'])
            except:
                con.rollback()
                msg.append("Error in insert operation!")
                error = True
            finally:
                return render_template("pages/profile.html", title="My Profile", message=msg, error=error,
                                       username=session['username'], account_data=account_data, updated=updated)
        if request.method == 'GET':
            return render_template('pages/profile.html', title="My profile", username=session['username'],
                                   account_data=account_data)


@app.route('/group/<url_key>')
def group(url_key):
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from groups where url_key=?', (url_key,))
            group_data = cursor.fetchone()

        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from posts where group_id=?', (group_data[0],))
        posts = cursor.fetchall()

        all = []
        for post in posts:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from accounts where id=?', (post[4],))
            account = cursor.fetchone()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=?', (int(post[0]),))
            likes = cursor.fetchall()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=? and user_id=?',
                               (int(post[0]), int(session['user_id']),))
            is_liked = cursor.fetchall()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from groups where id=?', (post[6],))
            group = cursor.fetchone()
            all.append(
                {'id': post[0], 'username': account[2], 'title': post[1],
                 'create_date': timeago.format(datetime.datetime.fromtimestamp(float(post[2])),
                                               datetime.datetime.now()), 'content': post[3],
                 'url_key': post[5], 'group': group[2], 'total_likes': str(len(likes)), 'is_liked': bool(is_liked)})

        return render_template('pages/group.html', title=group_data[1], username=session['username'],
                               posts=all)


@app.route('/create', methods=['POST', 'GET'])
def create():
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        msg = []
        error = False
        created = False

        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from groups')
            groups = cursor.fetchall()
        if request.method == 'POST':
            try:
                with sql.connect("database.db") as con:
                    cursor = con.cursor()
                    cursor.execute(
                        'INSERT INTO posts (title, create_date, content, user_id, url_key, group_id) VALUES(?, ?, ?, ?, ?, ?)',
                        (str(request.form['title']), str(time.time()), str(request.form['content']), session['user_id'],
                         str(request.form['title']).lower().replace(' ', '-'), str(request.form['school'])))
                    con.commit()
                    msg.append("Post created successfully!")
                    created = True
            except:
                con.rollback()
                msg.append("Error in insert operation! - Title already exists.")
                error = True
            finally:
                return render_template('pages/create.html', title="Create a post", username=session['username'],
                                       groups=groups, message=msg, error=error, created=created,
                                       url_key=str(request.form['title']).lower().replace(' ', '-'))
        if request.method == 'GET':
            return render_template("pages/create.html", title="Create a post", username=session['username'],
                                   groups=groups)


@app.route('/post/<url_key>')
def post(url_key):
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("select * from posts where url_key=?", (str(url_key),))
        post = cur.fetchone()

        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("select * from comments where post_id=?", (str(post[0]),))
        comments = cur.fetchall()

        all = []
        for comment in comments:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from accounts where id=?', (comment[3],))
            account = cursor.fetchone()

            all.append(
                {'username': account[2], 'content': comment[1],
                 'create_date': timeago.format(datetime.datetime.fromtimestamp(float(comment[4])),
                                               datetime.datetime.now())})

        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("select * from accounts where id=?", (post[4],))
        account = cur.fetchone()

        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from likes where post_id=?', (int(post[0]),))
        likes = cursor.fetchall()

        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("select * from groups where id=?", (post[6],))
        group = cur.fetchone()

        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from likes where post_id=? and user_id=?',
                           (int(post[0]), int(session['user_id']),))
        is_liked = cursor.fetchall()

        data = {'id': post[0], 'username': account[2], 'title': post[1],
                'create_date': timeago.format(datetime.datetime.fromtimestamp(float(post[2])),
                                              datetime.datetime.now()), 'content': post[3],
                'url_key': post[5], 'group': group[2], 'total_likes': str(len(likes)), 'is_liked': bool(is_liked)}

        return render_template("pages/post.html", title=post[1], username=session['username'], post_data=data,
                               comments=all)


@app.route('/user/<username>')
def user(username):
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from accounts where username=?', (username,))
            account = cursor.fetchone()

        with sql.connect("database.db") as con:
            cursor = con.cursor()
            cursor.execute('select * from posts where user_id=?', (account[0],))
        posts = cursor.fetchall()

        all = []
        for post in posts:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from groups where id=?', (post[6],))
            group = cursor.fetchone()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=?', (int(post[0]),))
            likes = cursor.fetchall()

            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute('select * from likes where post_id=? and user_id=?',
                               (int(post[0]), int(session['user_id']),))
            is_liked = cursor.fetchall()

            all.append(
                {'id': post[0], 'username': account[2], 'title': post[1],
                 'create_date': timeago.format(datetime.datetime.fromtimestamp(float(post[2])),
                                               datetime.datetime.now()), 'content': post[3],
                 'url_key': post[5], 'group': group[2], 'total_likes': str(len(likes)), 'is_liked': bool(is_liked)})

        return render_template('pages/user.html', title=account[2], username=session['username'],
                               posts=all, account_data=account,
                               account_create_date=timeago.format(datetime.datetime.fromtimestamp(float(account[7])),
                                                                  datetime.datetime.now()))


@app.route('/add_comment/<url>', methods=['POST'])
def add_comment(url):
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        try:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute(
                    'INSERT INTO comments (content, post_id, user_id, create_date) VALUES(?, ?, ?, ?)',
                    (str(request.form['content']), str(request.form['post_id']), str(request.form['user_id']),
                     str(time.time())))
                con.commit()
        except:
            con.rollback()
        finally:
            return redirect('/post/' + url)


@app.route('/vote/<post_id>/', methods=['POST'])
def like(post_id):
    if 'logged_in' not in session:
        return redirect("/login")
    else:
        try:
            with sql.connect("database.db") as con:
                cursor = con.cursor()
                cursor.execute(
                    'INSERT INTO likes (post_id, user_id) VALUES(?, ?)',
                    (int(post_id), int(session['user_id'])))
                con.commit()
        except:
            con.rollback()
        finally:
            return ""
