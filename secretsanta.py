#!/usr/bin/python

import random
import cherrypy
import os
import codecs
import shutil
import datetime

from jinja2 import Environment, FileSystemLoader

from auth import *

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "data")
env = Environment(loader=FileSystemLoader(
    os.path.join(current_dir,'templates'))
)

cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081,
                       })
 
config = {'/': {"tools.sessions.on" : True,
                "tools.sessions.storage_type" : "file",
                "tools.sessions.storage_path" : os.path.join(current_dir, "sessions"),
                "tools.sessions.timeout" : 60,
                "tools.staticdir.root" : os.path.join(current_dir, "sessions")},
          '/static': {"tools.staticdir.root" : os.path.join(current_dir, "static"),
                      "tools.staticdir.dir"  : ".",
                      "tools.staticdir.on"  : True}, }


def read_dict_file(filename, separator = ";"):
    with codecs.open(os.path.join(data_dir, filename), "r", encoding='utf-8') as f:
        return dict( line.rstrip().split(separator) for line in f if not line.startswith("#") )

def write_dict_file(filename, separator, dictionary, append = False):
    target = os.path.join(data_dir, filename)
    backup = os.path.join(data_dir, "%s.%s.bak" % (filename, datetime.datetime.now().strftime("%Y%m%d.%H%M%S")))
    shutil.copyfile(target, backup)

    with codecs.open(target, "w+" if append else "w", encoding='utf-8') as f:
        for (k,v) in dictionary.iteritems():
            f.write("%s%s%s\n" % (k, separator, v))

def read_passwords():
    return dict( (email.lower(), password) for (email, password) in read_dict_file("passwords.txt").iteritems() )

def read_names():
    return dict( (email.lower(), name) for (name, email) in read_dict_file("names.txt").iteritems() )

def read_groups():
    return dict( (email.lower(), group) for (email, group) in read_dict_file("groups.txt").iteritems() )


def read_pairs():
    return read_dict_file("pairs.txt")

def read_blacklist():
    return read_dict_file("blacklist.txt")

def read_wishlist():
    return read_dict_file("wishlist.txt")

def read_settings():
    return read_dict_file("settings.txt", ":")

def write_settings(settings):
    write_dict_file("settings.txt", ":", settings)


class AdminArea:
    
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group
    
    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    @cherrypy.expose
    def index(self):
        emails_enabled = (read_settings().get("emails_enabled", "False") == "True")
        tmpl = env.get_template( "admin.html" )
        return tmpl.render( emails_enabled=emails_enabled,
                            user_groups = cherrypy.session.get("user_groups", {}) )

    @cherrypy.expose
    def toggle_enable_emails(self):
        settings = read_settings()
        settings["emails_enabled"] = (settings.get("emails_enabled", "False") != "True")
        write_settings(settings)
        raise cherrypy.HTTPRedirect("/admin")


    @cherrypy.expose
    def names(self):
        return str(read_names())

    @cherrypy.expose
    def passwords(self):
        return str(read_passwords())

    @cherrypy.expose
    def pairs(self):
        return str(read_pairs())

    @cherrypy.expose
    def blacklist(self):
        return str(read_blacklist())

    @cherrypy.expose
    def wishlist(self):
        return str(read_wishlist())

    @cherrypy.expose
    def clearwishlist(self):
        write_dict_file("wishlist.txt", ";", {} )
        return "done"

    @cherrypy.expose
    def generate(self):

        givers = read_names().keys()
        takers = list(givers)

        blacklist_pairs = read_blacklist()

        while any(givers[i] == takers[i] or (givers[i], takers[i]) in blacklist_pairs for i in range(len(givers))):
            random.shuffle(takers)

        write_dict_file("pairs.txt", ";", dict( (givers[i], takers[i]) for i in range(len(givers)) ) )

        return "done"

class Root:
    
    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }
    
    auth = AuthController(env, read_passwords(), read_groups())
    
    admin = AdminArea()

    @cherrypy.expose
    @require(lambda: True)
    def index(self):
        names = read_names()        
        print names
        giver_full_name = names[cherrypy.request.login]
        pairs = read_pairs()
        recipient = pairs[cherrypy.request.login]        
        tmpl = env.get_template( "santa.html" )
        return tmpl.render( page="recipient", 
                            username=cherrypy.request.login, 
                            giver_forename=giver_full_name.split(" ")[0],
                            recipient_full_name=names[recipient],
                            recipient_forename=names[recipient].split(" ")[0],
                            user_groups = cherrypy.session.get("user_groups", {}) )

    @cherrypy.expose
    @require(lambda: True)
    def wishlist(self, user_wish = None):
        tmpl = env.get_template( "wishlist.html" )
        wishlist = read_wishlist()
        if user_wish:
            wishlist[cherrypy.request.login] = user_wish
            write_dict_file("wishlist.txt", ";", wishlist)
        else:
            user_wish = wishlist.get(cherrypy.request.login, "")

        names = read_names()           
        pairs = read_pairs()
        recipient = pairs[cherrypy.request.login]
        return tmpl.render( page="wishlist", 
                            username=cherrypy.request.login, 
                            wishlist=wishlist.values(), 
                            user_wish=user_wish,
                            recipient_forename=names[recipient].split(" ")[0] ,
                            user_groups = cherrypy.session.get("user_groups", {}) )

    @cherrypy.expose
    @require(lambda: True)
    def rules(self):
        tmpl = env.get_template( "rules.html" )
        return tmpl.render( page="rules", 
                            username=cherrypy.request.login,
                            user_groups = cherrypy.session.get("user_groups", {}) )


app = cherrypy.tree.mount(Root(), "/", config)
cherrypy.engine.start()
cherrypy.engine.block()
