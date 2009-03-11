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
    include_in_sitemap = db.BooleanProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Preferences(db.Model):
    anylitics_id = db.StringProperty()
        
class MainHandler(webapp.RequestHandler):
  def get(self):
    url = self.request.path
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    pages=db.GqlQuery("SELECT * FROM Page WHERE url = :1 LIMIT 1", url)
    
    if (pages.count() < 1):
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'error.html')
        self.response.set_status(404)
        self.response.out.write(template.render(path, {'url': url, 'is_admin': users.is_current_user_admin() }))

    else :
        page = pages.get()
        html=page.html
        title = page.title
        values = {
              'body' : html,
              'title' : title,
              'preferences' : preference_list.get(),
              'url': url, 
              'is_admin': users.is_current_user_admin()
                  }
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'content.html')
        self.response.out.write(template.render(path, values))
    #self.response.out.write(html)

class AdminHandler(webapp.RequestHandler):
  def get(self):
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    pages=db.GqlQuery("SELECT * FROM Page ORDER BY url")
    values = {
              'pages' : pages,
              'preferences' : preference_list.get(),
              'logout_url': users.create_logout_url("/"),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'admin.html')
    self.response.out.write(template.render(path, values))

class SitemapHandler(webapp.RequestHandler):
  def get(self):
    url = self.request.url
    pos = url.find('/', 9) # find the first / after the http:// part
    domian= url[:pos]
    pages=db.GqlQuery("SELECT * FROM Page where include_in_sitemap = True ORDER BY url")
    values = {
              'pages' : pages,
              'domain' :domian,
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'sitemap.xml')
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
    page.include_in_sitemap =  (self.request.get('include_in_sitemap', 'false') == 'true')
    page.put()
    self.redirect('/admin/')

class PreferencesHandler(webapp.RequestHandler):
  def post(self):
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    preferences = preference_list.get()
    if (preference_list.count() < 1):    
        preferences = Preferences()
    preferences.anylitics_id = self.request.get('anylitics_id')
    preferences.put()
    self.redirect('/admin/')

class EditHandler(webapp.RequestHandler):
  def get(self):
    button_html= '<form action="https://www.sandbox.paypal.com/cgi-bin/webscr" method="post"><input type="hidden" name="cmd" value="_xclick"><input type="hidden" name="business" value="{{ paypal_id }}"><input type="hidden" name="item_name" value="{{ item_name }}"><input type="hidden" name="amount" value="{{ price_dollars_cents }}"><input type="hidden" name="currency_code" value="AUD"><input type="hidden" name="no_shipping" value="1"><input type="hidden" name="rm" value="1"><input type="hidden" name="return" value="http://localhost:8080/purchase/completed/"><input type="hidden" name="cancel_return" value="http://localhost:8080/purchase/canceled/"><input type="hidden" name="bn" value="Breakup09_BuyNow_WPS_AU"><input type="image" src="https://www.sandbox.paypal.com/en_AU/i/btn/btn_buynowCC_LG.gif" border="0" name="submit" alt=""><img alt="" border="0" src="https://www.sandbox.paypal.com/en_AU/i/scr/pixel.gif" width="1" height="1"></form>'
    key_name = self.request.get('key')
    url = self.request.get('url')
    page={}
    if (key_name):
        page= db.get(db.Key(key_name))
    elif (url):
        pages=db.GqlQuery("SELECT * FROM Page WHERE url = :1 LIMIT 1", url)
        if (pages.count(1)>0):
            page=pages.get()
        else:
            page['url'] = url
    values = {
              'page' : page,
              'button_html' : button_html,
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit.html')
    self.response.out.write(template.render(path, values))


def main():
  application = webapp.WSGIApplication([('/admin/', AdminHandler),
                                        ('/admin/save/', SaveHandler),
                                        ('/admin/savePreferences/', PreferencesHandler),
                                        ('/admin/new/', EditHandler),
                                        ('/admin/edit/', EditHandler),
                                        ('/Sitemap.xml', SitemapHandler),
                                        ('.*', MainHandler),
                                        ])
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
