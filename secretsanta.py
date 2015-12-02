#!/usr/bin/python

import random
import os
import codecs
import shutil
import datetime
from functools import wraps

from jinja2 import Environment, FileSystemLoader

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask import session
from flask import redirect
from flask import url_for


app = Flask(__name__)
app.secret_key = 'SALKAS DFLkdaDSF&*5462SDAsd@E#'
app.config["APPLICATION_ROOT"] = "/secret-santa"


current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "data")
env = Environment(loader=FileSystemLoader(
    os.path.join(current_dir,'templates'))
)


def read_dict_file(filename, separator=";"):
    with codecs.open(os.path.join(data_dir, filename), "r", encoding='utf-8') as f:
        return dict(line.rstrip().split(separator) for line in f if not line.startswith("#"))


def write_dict_file(filename, separator, dictionary, append = False, header = ""):
    target = os.path.join(data_dir, filename)
    backup = os.path.join(data_dir, "%s.%s.bak" % (filename, datetime.datetime.now().strftime("%Y%m%d.%H%M%S")))
    shutil.copyfile(target, backup)

    with codecs.open(target, "w+" if append else "w", encoding='utf-8') as f:
        if header:
            f.write("%s\n" % header)
        for (k,v) in dictionary.iteritems():
            f.write("%s%s%s\n" % (k, separator, v))


def read_passwords():
    return dict( (email.lower(), password) for (email, password) in read_dict_file("passwords.txt").iteritems() )


def read_names():
    return dict( (email.lower(), name) for (name, email) in read_dict_file("names.txt").iteritems() )


def read_groups():
    return dict( (email.lower(), set(group.split(","))) for (email, group) in read_dict_file("groups.txt").iteritems() )


def read_pairs():
    return read_dict_file("pairs.txt")

def read_blacklist():
    previous_2012 = read_dict_file("pairs.2012.txt")
    previous_2013 = read_dict_file("pairs.2013.txt")
    return dict( previous_2012.items() + previous_2013.items() )


def read_wishlist():
    return read_dict_file("wishlist.txt")

def read_settings():
    return read_dict_file("settings.txt", ":")

def read_overrides():
    return dict( (giver.lower(), taker.lower()) for (giver, taker) in read_dict_file("overrides.txt").iteritems() )

def write_settings(settings):
    write_dict_file("settings.txt", ":", settings)


PASSWORDS = read_passwords()
GROUPS = read_groups()


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    username = username.lower()
    if PASSWORDS.get(username, None) != password:
        return False

    session["username"] = username
    return True


EMPTY_SET = set()


def user_groups(username):
    return GROUPS.get(username, EMPTY_SET)


def get_current_user_groups():
    return user_groups(session["username"])


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response("""Could not verify your access level for that URL.<br/>
You have to login with proper credentials""", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not get_current_user_groups().issuperset(set(roles)):
                return Response("Requires %s roles" % ",".join(roles), 403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


# -------------------------------------------------------------------------------------------------


@app.route("/auth/switchuser")
def auth_switchuser():
    return authenticate()


@app.route("/admin")
@requires_auth
@requires_roles("admin")
def admin_index():
    emails_enabled = (read_settings().get("emails_enabled", "False") == "True")
    return render_template("admin.html",
                           emails_enabled=emails_enabled,
                           user_groups=get_current_user_groups())

@app.route("/admin/toggle_enable_emails")
@requires_auth
@requires_roles("admin")
def admin_toggle_enable_emails():
    settings = read_settings()
    settings["emails_enabled"] = (settings.get("emails_enabled", "False") != "True")
    write_settings(settings)
    return redirect(url_for("admin_index"), code=302)


@app.route("/admin/names")
@requires_auth
@requires_roles("admin")
def admin_names():
    return str(read_names())


@app.route("/admin/passwords")
@requires_auth
@requires_roles("admin")
def admin_passwords():
    return str(read_passwords())


@app.route("/admin/pairs")
@requires_auth
@requires_roles("admin")
def admin_pairs():
    return render_template("pairs.html", 
                            pairs=read_pairs(),
                            username=session["username"], 
                            user_groups=get_current_user_groups())


@app.route("/admin/blacklist")
@requires_auth
@requires_roles("admin")
def admin_blacklist():
    return str(read_blacklist())


@app.route("/admin/wishlist")
@requires_auth
@requires_roles("admin")
def admin_wishlist():
    return str(read_wishlist())


@app.route("/admin/clearwishlist")
@requires_auth
@requires_roles("admin")
def admin_clearwishlist():
    write_dict_file("wishlist.txt", ";", {})
    return "done"


@app.route("/admin/generate")
@requires_auth
@requires_roles("admin")
def admin_generate():

    givers = read_names().keys()
    takers = list(givers)

    overrides = read_overrides()

    for (giver, taker) in overrides.iteritems():
        givers.remove(giver)
        takers.remove(taker)

    blacklist_pairs = read_blacklist().items()

    while any(giver == taker or (giver, taker) in blacklist_pairs for (giver, taker) in zip(givers, takers)):
        random.shuffle(takers)

    pairs = dict(zip(givers, takers))

    for (giver, taker) in overrides.iteritems():
        pairs[giver] = taker

    write_dict_file("pairs.txt", ";", pairs, header="# Giver;Taker")

    return redirect(url_for("admin_pairs"), code=302)


@app.route('/')
def index():
    if request.authorization:
        return redirect(url_for("recipient"), code=302)
    else:
        return redirect(url_for("welcome"), code=302)


@app.route('/welcome')
def welcome():
    return render_template("welcome.html", page="welcome")


@app.route('/participants')
@requires_auth
def participants():
    return render_template("participants.html",
                           page="participants",
                           names=read_names(),
                           username=session["username"],
                           user_groups = get_current_user_groups())


@app.route('/recipient')
@requires_auth
def recipient():
    names = read_names()        
    print names
    giver_full_name = names[session["username"]]
    pairs = read_pairs()
    recipient = pairs[session["username"]]
    return render_template("santa.html",
                           page="recipient",
                           username=session["username"],
                           giver_forename=giver_full_name.split(" ")[0],
                           recipient_full_name=names[recipient],
                           recipient_forename=names[recipient].split(" ")[0],
                           user_groups = get_current_user_groups())


@app.route("/wishlist", methods=['GET', 'POST'])
@requires_auth
def wishlist():
    user_wish = request.form.get("user_wish")
    wishlist = read_wishlist()
    if user_wish:
        wishlist[session["username"]] = user_wish
        write_dict_file("wishlist.txt", ";", wishlist)
        message = "Wishlist selection '%s' saved" % user_wish
    else:
        user_wish = wishlist.get(session["username"], "")
        message = ""

    names = read_names()           
    pairs = read_pairs()
    recipient = pairs[session["username"]]
    return render_template("wishlist.html",
                           page="wishlist",
                           username=session["username"],
                           wishlist=wishlist.values(),
                           user_wish=user_wish,
                           recipient_forename=names[recipient].split(" ")[0],
                           message=message,
                           user_groups=get_current_user_groups())


@app.route("/password-request", methods=['GET', 'POST'])
def password_request():
    username = request.form.get("username", "").strip().lower()
    password = PASSWORDS.get(username)
    if password:
        import emailutil
        emailutil.send([username],
                       "Secret Santa password", 
                       body_plain="""
Your password is:
%s
""" % password,
                       body_html="""
<p>Your password is:</p>
<p><pre>%s</pre><p/>
""" % password)
        message = "Password sent to %s" % username
        message_level = "important"
    else:
        message = "No account found for '%s'" % username
        message_level = "warning"

    return render_template("welcome.html", page="welcome", message=message, message_level=message_level)


@app.route("/rules")
@requires_auth
def rules():
    return render_template("rules.html",
                           page="rules",
                           username=session["username"],
                           user_groups=get_current_user_groups())


if __name__ == '__main__':
    # app.run(debug=True,
    #         host='0.0.0.0')




    # Relevant documents:
    # http://werkzeug.pocoo.org/docs/middlewares/
    # http://flask.pocoo.org/docs/patterns/appdispatch/
    from werkzeug.serving import run_simple
    from werkzeug.wsgi import DispatcherMiddleware
    app.config['DEBUG'] = True
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        app.config['APPLICATION_ROOT']: app,
    })
    run_simple('localhost', 5000, application, use_debugger=True, use_reloader=True)
