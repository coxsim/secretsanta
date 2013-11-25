#!/usr/bin/python


import cherrypy
import os
from jinja2 import Environment, FileSystemLoader

from auth import *

current_dir = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(
    os.path.join(current_dir,'templates'))
)


 
config = {'/': {"tools.sessions.on" : True,
                "tools.sessions.storage_type" : "file",
                "tools.sessions.storage_path" : os.path.join(current_dir, "sessions"),
                "tools.sessions.timeout" : 60}, }




class RestrictedArea:
    
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group
    
    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    @cherrypy.expose
    def index(self):
        return """This is the admin only area."""






class Root:
    
    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }
    
    auth = AuthController(env)
    
    restricted = RestrictedArea()

    
    @cherrypy.expose
    def open(self):
        return """This page is open to everyone"""
    
    @cherrypy.expose
    @require(name_is("joe"))
    def only_for_joe(self):
        return """Hello Joe - this page is available to you only"""

    # This is only available if the user name is joe _and_ he's in group admin
    @cherrypy.expose
    @require(name_is("joe"))
    @require(member_of("admin"))   # equivalent: @require(name_is("joe"), member_of("admin"))
    def only_for_joe_admin(self):
        return """Hello Joe Admin - this page is available to you only"""

    @cherrypy.expose
    @require(lambda: True)
    def index(self):
        tmpl = env.get_template( "santa.html" )
        return tmpl.render( username=cherrypy.request.login )




class Root2(object):
    @cherrypy.expose
    def index(self):
        tmpl = env.get_template( "index.html" )
        return tmpl.render(  )

    @cherrypy.expose
    def login(self, email, password):
    	with open("passwords", "r") as f:
    		passwords = dict( l.split(",") for l in f )

    	if password != passwords.get(email):
            pass


        tmpl = env.get_template( "index_logged_in.html" )
        return tmpl.render( email=email, password=password )


app = cherrypy.tree.mount(Root(), "/", config)
cherrypy.engine.start()
cherrypy.engine.block()