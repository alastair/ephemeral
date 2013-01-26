#!/usr/bin/python

import os
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web

import json
import datetime
from operator import itemgetter

import tweepy

CONSUMER_TOKEN = "pRyaURLzOFRbNc3n3mxg"
CONSUMER_SECRET = "ZTqGX4YDgVMnO5a7TP6tgVZRBfASmzEppDrrJa4u19Y"
CALLBACK = "http://umaster.org/twittercb"

class RootHandler(tornado.web.RequestHandler):

    def get(self):

        cookie = self.get_secure_cookie("current_user")
        if cookie:
            pass
        else:
            auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK)
            redirect_url = auth.get_authorization_url()
            self.set_secure_cookie("request_key", auth.request_token.key)
            self.set_secure_cookie("request_secret", auth.request_token.secret)

        return self.render('templates/index.html', url=redirect_url)

class TwitterHandler(tornado.web.RequestHandler):

    def get(self):
        verifier = self.get_argument("oauth_verifier")
        request_key = self.get_secure_cookie("request_key")
        request_secret = self.get_secure_cookie("request_secret")
        auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK)
        auth.set_request_token(request_key, request_secret)
        auth.get_access_token(verifier)

        access_key = auth.access_token.key
        access_secret = auth.access_token.secret

        self.redirect("/")

class LogoutHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect("/")

class ListHandler(tornado.web.RequestHandler):

    def get(self):
        return self.render('templates/index.html')

class ListenHandler(tornado.web.RequestHandler):

    def get(self):
        return self.render('templates/index.html')

class ShareHandler(tornado.web.RequestHandler):

    def get(self):
        return self.render('templates/index.html')

settings = {"static_path": os.path.join(os.path.dirname(__file__), "static"),
		"debug": True,
        "cookie_secret": "somecookievaluethatnooneknows"}
application = tornado.web.Application([(r"/", RootHandler),
    (r"/twcb", TwitterHandler),
    (r"/listen", ListHandler),
    (r"/listen/id", ListenHandler),
    (r"/share", ShareHandler)
	], **settings)

def main():
	server = tornado.httpserver.HTTPServer(application)
	server.listen(8090)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
