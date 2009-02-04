#!/usr/bin/env python
#
# First steps for easyweb, a content management system running on 
# appEngine.

import cgi
import os

import wsgiref.handlers


from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users

class Page(db.Model):
    url = db.StringProperty()
    title = db.StringProperty()
    html = db.TextProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    
class MainHandler(webapp.RequestHandler):
  def get(self):
    url = self.request.path
    pages=db.GqlQuery("SELECT * FROM Page WHERE url = :1 LIMIT 1", url)
    
    if (pages.count() < 1):
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'error.html')
        self.response.set_status(404)
        self.response.out.write(template.render(path, {'url': url }))

    else :
        page = pages.get()
        html=page.html
        title = page.title
        values = {
              'body' : html,
              'title' : title,
                  }
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'content.html')
        self.response.out.write(template.render(path, values))
    #self.response.out.write(html)

class AdminHandler(webapp.RequestHandler):
  def get(self):
    pages=db.GqlQuery("SELECT * FROM Page ORDER BY url")
    values = {
              'pages' : pages,
              'logout_url': users.create_logout_url("/"),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'admin.html')
    self.response.out.write(template.render(path, values))

class SaveHandler(webapp.RequestHandler):
  def post(self):
    key_name = self.request.get('key')
    page=Page()
    if (key_name):
        page= db.get(db.Key(key_name))
    page.url = self.request.get('url')
    page.title = self.request.get('title')
    page.html = self.request.get('html')
    page.put()
    self.redirect('/admin/')

class EditHandler(webapp.RequestHandler):
  def get(self):
    key_name = self.request.get('key')
    url = self.request.get('url')
    page={}
    if (key_name):
        page= db.get(db.Key(key_name))
    elif (url):
        page['url'] = url
    values = {
              'page' : page,
              }
    
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit.html')
    self.response.out.write(template.render(path, values))


def main():
  application = webapp.WSGIApplication([('/admin/', AdminHandler),
                                        ('/admin/save/', SaveHandler),
                                        ('/admin/new/', EditHandler),
                                        ('/admin/edit/', EditHandler),
                                        ('.*', MainHandler),
                                        ])
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
