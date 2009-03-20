#!/usr/bin/env python
#
# First steps for easyweb, a content management system running on 
# appEngine.

import cgi
import os
import re
import wsgiref.handlers
import logging
import mimetypes
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import mail

class Page(db.Model):
    url = db.StringProperty()
    title = db.StringProperty()
    html = db.TextProperty()
    include_in_sitemap = db.BooleanProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Preferences(db.Model):
    anylitics_id = db.StringProperty()
    paypal_id = db.StringProperty()

class Product(db.Model):
    name = db.StringProperty()
    price = db.StringProperty()
    return_url = db.StringProperty()
    return_cancel_url = db.StringProperty()
    file_name = db.StringProperty()
    file_ext = db.StringProperty()
    file_content = db.BlobProperty()

class Payment(db.Model):
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    payer_email = db.StringProperty()
    txn_id = db.StringProperty()
    item_name = db.StringProperty()
    verification_url = db.StringProperty()
    verification_result = db.StringProperty()
    all_values = db.TextProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    
class DownloadHandler(webapp.RequestHandler):
    def get(self):
        url = self.request.path
        match = re.match("/download/(.*)/", url)
        key=match.groups()[0]
        logging.debug ("key: %s" % key)
        product= db.get(key)
        if product.file_content:
            mimetypes.init()            
            #self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.headers['Content-Type'] = mimetypes.guess_type(product.file_name)[0]
            self.response.out.write(product.file_content)
        else:
            self.error(404)

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
    template_name = 'admin.html'
    url=self.request.path
    match = re.match("/admin/(.*)$", url)
    if match:
        my_file=match.groups()[0]
        logging.debug ("template: %s" % my_file)
        if my_file:
            template_name=my_file
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    pages=db.GqlQuery("SELECT * FROM Page ORDER BY url")
    products=db.GqlQuery("SELECT * FROM Product ORDER BY name")
    payments=db.GqlQuery("SELECT * FROM Payment ORDER BY creation_date")
    values = {
              'pages' : pages,
              'products' : products,
              'payments' : payments,
              'preferences' : preference_list.get(),
              'logout_url': users.create_logout_url("/"),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', template_name)
    self.response.out.write(template.render(path, values))

class TemplateHandler(webapp.RequestHandler):
  def get(self):
    url = self.request.url
    pos = url.find('/', 9) # find the first / after the http:// part
    domian= url[:pos]
    products=db.GqlQuery("SELECT * FROM Product ORDER BY name")
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    values = {
              'domain' :domian,
              'products' : products,
              'preferences' : preference_list.get(),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'fcktemplate.xml')
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
    self.redirect('/admin/pages.html')

class PreferencesHandler(webapp.RequestHandler):
  def post(self):
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    preferences = preference_list.get()
    if (preference_list.count() < 1):    
        preferences = Preferences()
    preferences.anylitics_id = self.request.get('anylitics_id')
    preferences.paypal_id = self.request.get('paypal_id')
    
    preferences.put()
    self.redirect('/admin/')
    
class ProductHandler(webapp.RequestHandler):
    def post(self):
        product = Product()
        product.name=self.request.get('product_name')
        product.price=self.request.get('product_price')
        product.return_url=self.request.get('product_return_url')
        product.return_cancel_url = self.request.get('product_return_cancel_url')
        product.file_name=self.request.get('product_file_name')
        product.file_ext=self.request.get('product_file_ext')
        #product.file_name=self.request.POST[u'product_file_upload'].filename
        my_content=self.request.get("product_file_upload")
        product.file_content=db.Blob(my_content)    
        product.put()
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


class FakePaymentHandler(webapp.RequestHandler):
    def post(self):
        payment = Payment()       
        payment.first_name = self.request.get('first_name')
        payment.last_name = self.request.get('last_name')
        payment.payer_email = self.request.get('payer_email')
        payment.txn_id = self.request.get('txn_id')
        payment.item_name = self.request.get('item_name')
        
        payment.verification_url = "fake"
        payment.verification_result = "fake"
        payment.all_values = self.request.get('all_values')
        payment.put()    
        self.redirect('/admin/')
        
class PaypalIPNHandler(webapp.RequestHandler):
    default_response_text = 'Nothing to see here'
    live_url = "https://www.paypal.com/cgi-bin/webscr"
    test_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'

    def post(self):
        self.get()
    def get(self):
        logging.debug('1')
        data = {}
        for i in self.request.arguments():
            data[i] = self.request.get(i)
        logging.debug('2')
            
        verify_url = self.live_url
        #if (data.get('test_ipn', '0')=='1'):
        verify_url = self.test_url
        data['cmd'] = '_notify-validate'
        result = self.do_post(verify_url, data)
        logging.debug('3')
 
        verified =  (result == 'VERIFIED')
        logging.debug('4')

        payment = Payment()
        r="huh?"
        if verified:
              r = "great"
        else:
              r = "badness"
        logging.debug('5')

        data['post+result'] = result 
        data['url+to+verify'] = verify_url

        logging.debug('6')
        payment = Payment()
        payment.first_name = self.request.get('first_name')
        payment.last_name = self.request.get('last_name')
        payment.payer_email = self.request.get('payer_email')
        payment.txn_id = self.request.get('txn_id')
        payment.item_name = self.request.get('item_name')
        
        payment.verification_url = verify_url
        payment.verification_result = result
        payment.all_values = dict_to_string(data)
        payment.put()
        logging.debug('7')

        message = mail.EmailMessage(sender='hcurrie@gmail.com',
                            subject='[IPN] process ' + r,
                            to = 'hcurrie@gmail.com',
                            body = dict_to_string(data))
        logging.debug('8')
        message.send()
        logging.debug('9')
        ### TODO: send email to user with download instructions
        
        self.response.out.write(r)

    def do_post(self, url, args):
        return urlfetch.fetch(
            url = url,
            method = urlfetch.POST,
            payload = urllib.urlencode(args)
        ).content

    def verify(self, data):
        verify_url = self.live_url
        if (data.get('test_ipn', '0')=='1'):
            verify_url = self.test_url
        args = {
            'cmd': '_notify-validate',
        }
        args.update(data)
        result = self.do_post(verify_url, args) 
        r = {'post_result': result }
        r.update(data)
        return  result == 'VERIFIED'
    
def dict_to_string(dict):
    s=""
    for key in dict.keys():
        s="%s %s : %s \n" %(s,key,dict[key])
    return s

def main():
  application = webapp.WSGIApplication([('/admin/[a-z]*.html', AdminHandler),
                                        ('/admin/', AdminHandler),
                                        ('/admin/save/', SaveHandler),
                                        ('/admin/savePreferences/', PreferencesHandler),
                                        ('/admin/saveProduct/', ProductHandler),
                                        ('/admin/savePayment/', FakePaymentHandler),
                                        ('/admin/new/', EditHandler),
                                        ('/admin/edit/', EditHandler),
                                        ('/download/.*', DownloadHandler),
                                        ('/Sitemap.xml', SitemapHandler),
                                        ('/fcktemplate.xml', TemplateHandler),
                                        ('/purchase/ipn/', PaypalIPNHandler),
                                        ('.*', MainHandler),
                                        ])
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
