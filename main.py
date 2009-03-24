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

from easywebmodels import *
    
class DownloadHandler(webapp.RequestHandler):
    def get(self):
        url = self.request.path
        match = re.match("/download/(.*)/", url)
        key=match.groups()[0]
        logging.debug ("key: %s" % key)
        payment = db.get(key)
        product = db.get(payment.product_key)
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
    self.redirect('/admin/preferences.html')
    
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
        self.redirect('/admin/book.html')

class EditHandler(webapp.RequestHandler):
  def get(self):
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
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit.html')
    self.response.out.write(template.render(path, values))

class AdminRedirector(webapp.RequestHandler):
    def post(self):
        self.get()
    def get(self):
        self.redirect('/admin/pages.html')

class FakePaymentHandler(webapp.RequestHandler):
    def post(self):
        payment = Payment()       
        payment.first_name = self.request.get('first_name')
        payment.last_name = self.request.get('last_name')
        payment.payer_email = self.request.get('payer_email')
        payment.txn_id = self.request.get('txn_id')
        payment.item_name = self.request.get('item_name')

        payment.product_key = self.request.get('product_key')
        payment.mc_gross = self.request.get('mc_gross')
        
        payment.verification_url = "fake"
        payment.verification_result = self.request.get('verification_result')
        payment.all_values = self.request.get('all_values')
        payment.put()    
        self.redirect('/admin/purchases.html')
        
class PaypalIPNHandler(webapp.RequestHandler):
    live_url = "https://www.paypal.com/cgi-bin/webscr"
    test_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'

    def get_verification_url(self, data):
        verification_url = self.live_url
        if (self.request.get('test_ipn', '0') == '1'):
            verification_url = self.test_url     
        data['verification+url'] = verification_url   
        return verification_url

    def post(self):
        self.get()
    def get(self):
        data = {}
        for i in self.request.arguments():
            data[i] = self.request.get(i)
        data['cmd'] = '_notify-validate'
            
        verification_url = self.get_verification_url(data)
        result = self.do_post(verification_url, data)
        data['ipn+post+result'] = result
        ipn_verified =  (result == 'VERIFIED')

        product_key = self.request.get('item_number')
        product = db.get(db.Key(product_key))
        
        paypal_price = self.request.get('mc_gross')
        product_price = product.price
        data['paypal+price'] =  paypal_price
        data['product+price'] = product_price
        price_verified = (paypal_price == product_price)

        verified = (ipn_verified and price_verified)
            
        payment = Payment()
        payment.first_name = self.request.get('first_name')
        payment.last_name = self.request.get('last_name')
        payment.payer_email = self.request.get('payer_email')
        payment.txn_id = self.request.get('txn_id')
        payment.item_name = self.request.get('item_name')
        payment.product_key = self.request.get('item_number')
        payment.mc_gross = self.request.get('mc_gross')
        
        payment.verification_url = verification_url
        if verified:
            payment.verification_result = "Success"
        else:
            payment.verification_result = "Failure"
        payment.all_values = dict_to_string(data)
        payment.put()

        url = self.request.url
        pos = url.find('/', 9) # find the first / after the http:// part
        domain= url[:pos]
            
        template_values = {
            'payment'     : payment,
            'product'     : product,
            'ipn_verified': ipn_verified,
            'price_verified': price_verified,
            'variables'   : dict_to_string(data),
            'domain'      : domain,
        }

        subject=''
        body=''
        sender='hcurrie@gmail.com'
        to = 'hcurrie@gmail.com'
        if verified:
            # send email to user
            subject = "Verification Success"
            path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'purchase_complete_email.html')
            body = template.render(path, template_values)
            #to = payment.payer_email
        else:
            # send email to admin
            subject = "Verification Failure"
            path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'purchase_validation_error_email.html')
            body = template.render(path, template_values)
        message = mail.EmailMessage(sender=sender, subject=subject, to = to, body = body)
        message.send()            
        
        self.response.out.write('processing complete')

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
                                        ('/admin/', AdminRedirector),
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
