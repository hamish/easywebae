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
 
class StandardPageHandler(webapp.RequestHandler):
    pass
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
              'template_name': template_name,
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
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'myCKtemplates.js')
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
    preferences.paypal_sandbox_id = self.request.get('paypal_sandbox_id')
    preferences.admin_email = self.request.get('admin_email')
    
    preferences.put()
    self.redirect('/admin/preferences.html')
    
class ProductHandler(webapp.RequestHandler):
    def post(self):
        key_name = self.request.get('key')
        product = Product()
        if (key_name):
            product= db.get(db.Key(key_name))
        product.name=self.request.get('product_name')
        product.price=self.request.get('product_price')
        product.return_url=self.request.get('product_return_url')
        product.return_cancel_url = self.request.get('product_return_cancel_url')
        product.sucess_email_subject = self.request.get('sucess_email_subject')
        product.sucess_email_body = self.request.get('sucess_email_body')
        file_name = self.request.get('product_file_name')
        if file_name:
            product.file_name=file_name
            product.file_ext=self.request.get('product_file_ext')
            #product.file_name=self.request.POST[u'product_file_upload'].filename
            my_content=self.request.get("product_file_upload")
            product.file_content=db.Blob(my_content)
        else:
            logging.info("file not set - ignoring")
        product.put()        
        self.redirect('/admin/book.html')
        
class EditProductHandler(webapp.RequestHandler):
  def get(self):
    key_name = self.request.get('key')
    product={}
    if (key_name):
        product= db.get(db.Key(key_name))
    preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
    pages=db.GqlQuery("SELECT * FROM Page ORDER BY url")
    products=db.GqlQuery("SELECT * FROM Product ORDER BY name")
    payments=db.GqlQuery("SELECT * FROM Payment ORDER BY creation_date")
    values = {
              'pages' : pages,
              'preferences' : preference_list.get(),
              'logout_url': users.create_logout_url("/"),
              'product' : product,
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit_product.html')
    self.response.out.write(template.render(path, values))

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

        
class PaypalIPNHandler(webapp.RequestHandler):
    live_url = "https://www.paypal.com/cgi-bin/webscr"
    test_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'

    def get_verification_url(self, data):
        verification_url = self.live_url
        if (self.request.get('test_ipn', '0') == '1'):
            verification_url = self.test_url     
        data['verification+url'] = verification_url   
        return verification_url

    def is_price_valid(self, data, product):
        paypal_price = self.request.get('mc_gross')
        product_price = product.price
        data['paypal+price'] =  paypal_price
        data['product+price'] = product_price
        price_verified = (paypal_price == product_price)    
        return price_verified
        
    def is_ipn_valid(self, data):
        data['cmd'] = '_notify-validate'
            
        verification_url = self.get_verification_url(data)
        result = self.do_post(verification_url, data)
        data['ipn+post+result'] = result
        ipn_verified =  (result == 'VERIFIED')
        return ipn_verified
    
    def post(self):
        self.get()
    def get(self):
        self.process_ipn(1)
    def process_ipn(self, do_paypal_verification):
        preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
        preferences = preference_list.get()

        data = {}
        for i in self.request.arguments():
            data[i] = self.request.get(i)

        product_key = self.request.get('custom')
        logging.info("key = " + product_key)
        product = db.get(db.Key(product_key))

        ipn_verified = (1==1)
        if do_paypal_verification:
            ipn_verified = self.is_ipn_valid(data)
        else:
            ipn_verified = (self.request.get('paypal_verification') == 'Success')
        price_verified = self.is_price_valid(data, product)

        verified = (ipn_verified and price_verified)
            
        payment = Payment()
        payment.first_name = self.request.get('first_name')
        payment.last_name = self.request.get('last_name')
        payment.payer_email = self.request.get('payer_email')
        payment.txn_id = self.request.get('txn_id')
        payment.item_name = self.request.get('item_name')
        payment.product_key = product_key
        payment.mc_gross = self.request.get('mc_gross')
        
        payment.verification_url = self.get_verification_url(data)
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
        sender = preferences.admin_email
        to = preferences.admin_email
        link_token = '<img src="/static/admin/images/insert_link_here.png" alt="" />'
        link= "%s/download/%s/%s" %( domain, payment.key(), product.file_name)
        if verified:
            # send email to user
            subject = product.sucess_email_subject
            tmp_body=product.sucess_email_body            
            body = tmp_body.replace(link_token, link)
            to = payment.payer_email
        else:
            # send email to admin
            subject = "Verification Failure"
            path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'purchase_validation_error_email.html')
            body = template.render(path, template_values)
        message = mail.EmailMessage(sender=sender, subject=subject, to=to, body=body, )
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

class FakePaymentHandler(PaypalIPNHandler):
    def post(self):
        self.process_ipn(0)
        self.redirect('/admin/purchases.html')
    
def dict_to_string(dict):
    s=""
    for key in dict.keys():
        s="%s %s : %s \n" %(s,key,dict[key])
    return s

def main():
  application = webapp.WSGIApplication([('/admin/[a-z]*.html', AdminHandler),
                                        ('/admin/?', AdminRedirector),
                                        ('/admin/save/', SaveHandler),
                                        ('/admin/savePreferences/', PreferencesHandler),
                                        ('/admin/saveProduct/', ProductHandler),
                                        ('/admin/editProduct/', EditProductHandler),
                                        ('/admin/savePayment/', FakePaymentHandler),
                                        ('/admin/new/', EditHandler),
                                        ('/admin/edit/', EditHandler),
                                        ('/download/.*', DownloadHandler),
                                        ('/Sitemap.xml', SitemapHandler),
                                        ('/fcktemplate.xml', TemplateHandler),
                                        ('/myCKtemplates.js', TemplateHandler),
                                        ('/purchase/ipn/', PaypalIPNHandler),
                                        ('.*', MainHandler),
                                        ])
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
