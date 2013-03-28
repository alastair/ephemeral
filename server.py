#!/usr/bin/python

import os
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
import mimetypes
import datetime
import random

import tweepy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import desc

import models
engine = create_engine('mysql://ephemeral:fdsov08*(y7fkjfdskirujfs093r@localhost/ephemeral')
DbSession = scoped_session(sessionmaker(bind=engine))

CONSUMER_TOKEN = "pRyaURLzOFRbNc3n3mxg"
CONSUMER_SECRET = "ZTqGX4YDgVMnO5a7TP6tgVZRBfASmzEppDrrJa4u19Y"
CALLBACK = "http://ephemeralplayback.com/twitter"

def get_twitter_api_for_user(session, username):
    user = session.query(models.User).filter(models.User.screen_name==username).first()
    if user is None:
        return None
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    auth.set_access_token(user.key, user.secret)
    api = tweepy.API(auth)
    return api

def share(session, song, fr, to):
    f_user = session.query(models.User).filter(models.User.screen_name==fr).first()
    t_user = session.query(models.User).filter(models.User.screen_name==to).first()
    share = models.Share()
    share.user_from_id = f_user.id
    share.user_to_id = t_user.id
    share.song_id = song.id
    share.date_shared = datetime.datetime.utcnow()
    # Get the twitter user information, see how twitter-famous they are to see
    # how many plays/shares they get
    api = get_twitter_api_for_user(session, to)
    followers = api.me().followers_count
    numshares = 1
    if followers > 5000:
        numshares = 3
    elif followers > 2000:
        numshares = 2
    share.numplays = numshares
    share.numshares = numshares

    pc = models.PlayCode(song.id)
    session.add(pc)
    session.add(share)
    session.commit()
    return (f_user.id, t_user.id)

class RootHandler(tornado.web.RequestHandler):

    def get(self):
        session = DbSession()
        args = {}

        username = self.get_secure_cookie("session")
        api = get_twitter_api_for_user(session, username)
        if username and not api:
            self.clear_cookie("session")
            self.redirect("/")

        # Not logged in, need a twitter url
        if username is None:
            auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK)
            redirect_url = auth.get_authorization_url()
            self.set_secure_cookie("request_key", auth.request_token.key)
            self.set_secure_cookie("request_secret", auth.request_token.secret)
            args["url"] = redirect_url
            args["logged_in"] = False
        else:
            # Logged in
            me = api.me()
            args["name"] = me.screen_name
            args["logged_in"] = True

        song = session.query(models.Song).filter(models.Song.active==True).first()
        if song:
            args["pastsong"] = True
            args["title"] = song.title
            args["artist"] = song.artist
            listener = session.query(models.Share).filter(models.Share.song_id==song.id).order_by(desc(models.Share.date_shared)).first()
            if listener:
                args["who"] = listener.user_to.screen_name
                wants = session.query(models.Want).filter(models.Want.song_id==song.id).filter(models.Want.wanted_from_id==listener.user_to_id).count()
                args["numwants"] = wants
                oldwants = session.query(models.Want).filter(models.Want.song_id==song.id).filter(models.Want.wanted_from_id!=listener.user_to_id).count()
                args["oldwants"] = oldwants
                if args["logged_in"] and args["name"] == listener.user_to.screen_name:
                    # The song is ours
                    doneplays = session.query(models.Play).filter(models.Play.song_id==song.id).filter(models.Play.user_id==listener.user_to.id)
                    doneshares = session.query(models.Share).filter(models.Share.song_id==song.id).filter(models.Share.user_from_id==listener.user_to.id)
                    args["doneshares"] = doneshares.count()
                    args["doneplays"] = doneplays.count()
                    args["allowedplays"] = listener.numplays
                    args["allowedshares"] = listener.numshares
                    args["ours"] = True
                    args["nummoreshares"] = args["allowedshares"] - args["doneshares"]
                    args["nummoreplays"] = args["allowedplays"] - args["doneplays"]
                    print "doneplays", doneplays.count()
                    print "wantplay", listener.numplays
                    print ""
                    if args["doneplays"] >= args["allowedplays"]:
                        # If we've played as many as we can, find people to share them to
                        wants = session.query(models.Want).filter(models.Want.song_id==song.id).all()
                        wants = [w for w in wants if w.user.screen_name !=username]
                        wants = random.sample(wants, min(len(wants), 3))
                        wantprofiles = []
                        for w in wants:
                            wantprofiles.append(api.get_user(screen_name=w.user.screen_name))
                        suggestions = me.followers_ids()
                        suggestions = random.sample(suggestions, min(len(suggestions), 3))
                        sugprofiles = []
                        for s in suggestions:
                            sugprofiles.append(api.get_user(id=s))
                        args["sugprofiles"] = sugprofiles
                        args["wantprofiles"] = wantprofiles
                    else:
                        # Get the playcode
                        pc = session.query(models.PlayCode).filter(models.PlayCode.song_id==song.id).filter(models.PlayCode.played==False).first()
                        args["playcode"] = pc.code
                else:
                    args["ours"] = False

            else:
                args["pastsong"] = False

        return self.render('templates/index.html', **args)

class TwitterHandler(tornado.web.RequestHandler):

    def get(self):
        session = DbSession()
        verifier = self.get_argument("oauth_verifier")
        request_key = self.get_secure_cookie("request_key")
        request_secret = self.get_secure_cookie("request_secret")
        auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK)
        auth.set_request_token(request_key, request_secret)
        auth.get_access_token(verifier)

        access_key = auth.access_token.key
        access_secret = auth.access_token.secret
        api = tweepy.API(auth)
        me = api.me()
        screen_name = me.screen_name
        print "logged in", screen_name

        users = session.query(models.User).filter(models.User.screen_name==screen_name)

        if users.count() == 0:
            user = models.User()
            user.screen_name = screen_name
        else:
            user = users[0]
        user.key = access_key
        user.secret = access_secret

        session.add(user)
        session.commit()

        self.set_secure_cookie("session", screen_name)

        self.redirect("/")

class LogoutHandler(tornado.web.RequestHandler):

    def get(self):
        self.clear_cookie("session")
        self.redirect("/")

class CurrentHandler(tornado.web.RequestHandler):
    def get(self, thing):
        session = DbSession()
        song = session.query(models.Song).filter(models.Song.active==True).first()
        if song is None:
            raise tornado.web.HTTPError(404, 'No current song')
        if thing == "image":
            imgpath = song.image
            mime = mimetypes.guess_type(imgpath)[0]
            self.set_header("Content-Type", mime)

            self.write(open(imgpath, "rb").read())
            self.finish()
        elif "mp3" in thing:
            codestr = thing.replace(".mp3", "")
            code = session.query(models.PlayCode).filter(models.PlayCode.code==codestr).filter(models.PlayCode.played==False).first()
            if code:
                code.played = True
                session.add(code)
                newpc = models.PlayCode(code.song_id)
                session.add(newpc)
                lastshare = session.query(models.Share).filter(models.Share.song_id==song.id).order_by(desc(models.Share.date_shared)).first()
                if lastshare:
                    user = lastshare.user_to_id
                    play = models.Play()
                    play.user_id = user
                    play.song_id = song.id
                    date_played = datetime.datetime.now()
                    session.add(play)
                session.commit()

            songpath = song.path
            mime = mimetypes.guess_type(songpath)[0]
            self.set_header("Content-Type", mime)

            self.write(open(songpath, "rb").read())
            self.finish()

class WantHandler(tornado.web.RequestHandler):
    def get(self):
        session = DbSession()
        username = self.get_secure_cookie("session")
        api = get_twitter_api_for_user(session, username)
        user = session.query(models.User).filter(models.User.screen_name==username).first()
        if username is None or api is None or user is None:
            self.redirect("/")

        args = {}
        currentsong = session.query(models.Song).filter(models.Song.active==True).first()
        if currentsong:
            args["title"] = currentsong.title
        listener = session.query(models.Share).filter(models.Share.song_id==currentsong.id).order_by(desc(models.Share.date_shared)).first()
        if listener:
            args["who"] = listener.user_to.screen_name
        message = "@%s please share %s to me" % (args["who"], args["title"])
        args["tweet"] = message
        args["song_id"] = currentsong.id
        args["user_id"] = user.id
        args["wanted_from_id"] = listener.user_to_id

        cur = session.query(models.Want).filter(models.Want.song_id==currentsong.id).filter(models.Want.user_id==user.id).filter(models.Want.wanted_from_id==listener.user_to_id)
        args["alreadywanted"] = cur.count() > 0
        return self.render('templates/want.html', **args)

    def post(self):
        session = DbSession()
        username = self.get_secure_cookie("session")
        api = get_twitter_api_for_user(session, username)
        message = self.get_argument("tweet")
        if "#ephemeralplayback" not in message:
            message = "%s #ephemeralplayback" % (message,)
        wanted_from_id = self.get_argument("wanted_from_id")
        user_id = self.get_argument("user_id")
        song_id = self.get_argument("song_id")
        url = "http://ephemeralplayback.com/link?song=%s&from=%s&to=%s" % (song_id, user_id, wanted_from_id)
        if "http://eph" not in message:
            message = "%s %s" % (message, url)
        print "Asing message", message
        try:
            api.update_status(message)
        except:
            pass
        want = models.Want()
        want.user_id = user_id
        want.wanted_from_id = wanted_from_id
        want.song_id = song_id
        want.date_wanted = datetime.datetime.utcnow()
        session.add(want)
        session.commit()
        self.redirect("/")

class LatestHandler(tornado.web.RequestHandler):
    def get(self):
        return self.render('templates/index.html')

class ShareHandler(tornado.web.RequestHandler):
    def get(self, shareto):
        session = DbSession()
        if not shareto:
            shareto = self.get_argument("to", None)
        if not shareto:
            self.redirect("/?nouser")

        # Just check if they're real
        username = self.get_secure_cookie("session")
        api = get_twitter_api_for_user(session, username)
        user = api.get_user(shareto)
        if user is None:
            self.redirect("/?nosuchuser")

        # Make the share
        # Assume it's the only active song that's being played
        # XXX If more than 1 song, fix this
        song = session.query(models.Song).filter(models.Song.active==True).first()
        (fromid, toid) = share(session, song, username, shareto)

        # Send tweet!
        url = "http://ephemeralplayback.com/link?song=%s&from=%s&to=%s" % (song.id, fromid, toid)
        message = "I just shared %s to @%s on #ephemeralplayback %s" % (song.title, shareto, url)
        try:
            api.update_status(message)
        except:
            pass

        self.redirect("/")
        print "shareto",shareto

class GraphHandler(tornado.web.RequestHandler):
    def get(self, songid):
        pass

class AboutHandler(tornado.web.RequestHandler):
    def get(self):
        return self.render('templates/about.html')

class LinkHandler(tornado.web.RequestHandler):
    def get(self):
        session = DbSession()
        song = self.get_argument("song", None)
        u_from = self.get_argument("from", None)
        u_to = self.get_argument("to", None)

        click = models.Click()
        click.date_clicked = datetime.datetime.utcnow()
        click.ip = self.request.headers.get('X-Forwarded-For')
        click.song_id = song
        click.tweet_user_id = u_from
        click.tweet_target_id = u_to

        username = self.get_secure_cookie("session")
        if username:
            user = session.query(models.User).filter(models.User.screen_name==username).first()
            if user:
                click.user_id = user.id

        session.add(click)
        session.commit()
        self.redirect("/")

class AddHandler(tornado.web.RequestHandler):
    def get(self):
        session = DbSession()
        username = self.get_secure_cookie("session")
        if username:
            users = session.query(models.User).filter(models.User.screen_name==username)
            # If user is none then we have a session set but no user exists in the database.
            #   in this case, delete the cookie and reload
            if users.count() == 0:
                self.clear_cookie("session")
                self.redirect("/")
            user = users[0]
            auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
            auth.set_access_token(user.key, user.secret)
            api = tweepy.API(auth)
            me = api.me()
            #if me.screen_name != 'alastairporter':
            #    raise tornado.web.HTTPError(403, 'Access deniend')

            songs = session.query(models.Song).filter(models.Song.active==True)
            args = {}
            if songs.count() > 0:
                args["pastsong"] = True
                args["title"] = songs[0].title
                args["artist"] = songs[0].artist
            else:
                args["pastsong"] = False

            return self.render('templates/add.html', **args)
        else:
            raise tornado.web.HTTPError(403, 'Whoops')

    def post(self):
        # Set last inactive song to active
        session = DbSession()
        old = session.query(models.Song).filter(models.Song.active==True).first()
        if old:
            old.active = False
            session.add(old)
            session.commit()
        cover = self.request.files.get("cover")
        song = self.request.files.get("song")
        title = self.get_argument("title")
        artist = self.get_argument("artist")
        who = self.get_argument("who")
        if cover is None or song is None or len(cover) == 0 or len(song) == 0:
            raise tornado.web.HTTPError(500, 'Not the right data')
        cover = cover[0]
        song = song[0]
        s = models.Song()
        s.title = title
        s.artist = artist
        s.active = True
        session.add(s)
        session.commit()
        s_id = s.id
        path = os.path.join("files", "%s" % s_id)
        os.mkdir(path)
        cover_fname = os.path.join(path, os.path.basename(cover["filename"]))
        song_fname = os.path.join(path, os.path.basename(song["filename"]))
        s.path = song_fname
        s.image = cover_fname
        open(song_fname, "wb").write(song["body"])
        open(cover_fname, "wb").write(cover["body"])
        session.add(s)
        session.commit()
        share(session, s, "ephemeralplayback", who)
        session.close()

        self.redirect("/add")

settings = {"static_path": os.path.join(os.path.dirname(__file__), "static"),
        "debug": True,
        "cookie_secret": "somecookievaluethatnooneknows"}
application = tornado.web.Application([
    (r"/", RootHandler),
    (r"/twitter", TwitterHandler),
    (r"/logout", LogoutHandler),
    (r"/share(?:/(.*))?", ShareHandler),
    (r"/add", AddHandler),
    (r"/want", WantHandler),
    (r"/current/(.*)", CurrentHandler),
    (r"/graph/(.*)", GraphHandler),
    (r"/link", LinkHandler),
    (r"/about", AboutHandler),
    ], **settings)

def main():
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
