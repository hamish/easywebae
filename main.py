#!/usr/bin/env python
#

import cgi
import os
import re
import wsgiref.handlers
import logging
import mimetypes
import urllib
import email

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import mail

from easywebmodels import *


from BeautifulSoup import BeautifulSoup, Tag, NavigableString
#### Base Class #######
class EasywebRequestHandler(webapp.RequestHandler):
    def get_preferences(self):
        preference_list = db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
        preferences=Preferences()
        if (preference_list.count() > 0):
            preferences = preference_list.get()
        return preferences
    def get_domain(self):
        domain_url = self.request.url
        pos = domain_url.find('/', 9) # find the first / after the http:// part
        domain= domain_url[:pos]
        return domain
    def get_page_for_write(self, url, type='Sales'):
        pages=db.GqlQuery("SELECT * FROM Page WHERE url = :1 LIMIT 1", url)
        page = pages.get()
        if not page:
            page=Page(type=type)
            page.url=url
        return page
        
#### END Base Class #######
            
class UserProductHandler(EasywebRequestHandler):

    def redirect_to_product_payment(self, product, domain):
        #preference_list = db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
        preferences = self.get_preferences()
        parameters = {
                      "business": "%s" % preferences.paypal_id, 
                      "cmd": "_xclick", 
                      "item_name": "%s" % product.name, 
                      "custom": "%s" % product.key, 
                      "amount": "%s" % product.price, 
                      "currency_code": "USD", 
                      "no_shipping": "1", 
                      "rm": "1", 
                      "return": "%s%s" % (domain, product.return_url), 
                      "cancel_return": "%s%s" % (domain, product.return_cancel_url), 
                      "bn": "Breakup09_BuyNow_WPS_AU", 
                      "notify_url": "%s%s" % (domain, "/purchase/ipn/")
        }
        parameters_encoded = urllib.urlencode(parameters)
        paypal_url = "https://www.paypal.com/cgi-bin/webscr?"
        payment_link = paypal_url + parameters_encoded
        logging.info("redirect to:" + payment_link)
        self.redirect(payment_link)

    def get(self):
        domain= self.get_domain()           
        url = self.request.path
        id=''
        match = re.match("/product/([0-9]*)/?", url)
        if match:
            id=match.groups()[0]
        if id:
            key = db.Key.from_path('Product', int(id))
            logging.info(key)
            product = db.get(key)
            if product:
                self.redirect_to_product_payment(product, domain)
            else:
                self.response.out.write ("No corresponding product in database for id: " + id)                
        else:
            product_list=db.GqlQuery("SELECT * FROM Product order by creation_date DESC LIMIT 1")
            product= product_list.get()
            if product:
                logging.info("/product/ called with no id - using id: %s" % product.key().id())
                self.redirect_to_product_payment(product, domain)
            else:
                self.response.out.write ("Unable to find the ebook you wish to purchase")
            
class DownloadHandler(EasywebRequestHandler):   
    def get(self):
        url = self.request.path
        match = re.match("/download/(.*)/", url)
        key=match.groups()[0]
        logging.debug ("key: %s" % key)
        payment = db.get(key)
        product = db.get(payment.product_key)
        if product.file_content:
            mimetypes.init()
            self.response.headers['Content-Type'] = mimetypes.guess_type(product.file_name)[0]
            self.response.out.write(product.file_content)
        else:
            self.error(404)
class StyleHandler(EasywebRequestHandler):
  def get(self):
        domain= self.get_domain()           
        url = self.request.path
        id=''
        match = re.match("/style/([a-zA-Z0-9]*).css", url)
        if match:
            id=match.groups()[0]
        if id:
            key = db.Key(id)
            logging.info("Style: %s" % key)
            style = db.get(key)
            if style:
                encoding = mimetypes.guess_type(url)[0]
                if encoding:
                    self.response.headers['Content-Type'] = encoding
                self.response.out.write (style.content)
            else:
                self.response.set_status(404)
                self.response.out.write ("No corresponding style in database for id: " + id)                
        else:
            self.response.set_status(404)
            self.response.out.write ("Style not found")

class MainHandler(EasywebRequestHandler):
  def get(self):
    url = self.request.path
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
              'page' : page,
              'body' : html,
              'title' : title,
              'preferences' : self.get_preferences(),
              'url': url, 
              'is_admin': users.is_current_user_admin()
                  }
        encoding = mimetypes.guess_type(url)[0]
        if encoding:
            self.response.headers['Content-Type'] = encoding
            logging.info("setting encoding to: %s" % encoding)
        if (not encoding or encoding=='text/html'):
            logging.info("template")
            path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'tracker.js')
            tracker=template.render(path, values)
            end_body_loc = html.rfind('</body')
            new="%s%s%s" % (html[:end_body_loc], tracker, html[end_body_loc:])
            
#            path1 = os.path.join(os.path.dirname(__file__),'easyweb-core', 'tracker1.js')
#            tracker1=template.render(path1, values)
#            path2 = os.path.join(os.path.dirname(__file__),'easyweb-core', 'tracker2.js')
#            tracker2=template.render(path2, values)
#            soup = BeautifulSoup(html)
#            s1=Tag(soup, "script")
#            s1['type']="text/javascript"
#            t1=NavigableString(tracker1)
#            s1.insert(0, t1)
#            soup.html.body.insert(len(soup.html.body), s1)
#            
#            s2=Tag(soup, "script")
#            s2['type']="text/javascript"
#            t2=NavigableString(tracker2)
#            s2.insert(0, t2)
#            soup.html.body.insert(len(soup.html.body), s2)

            #self.response.out.write("%s"%soup)
            #self.response.out.write(html)
            self.response.out.write(new)
        else:
            logging.info("raw")
            self.response.out.write(html)

class FckConnectorHandler(EasywebRequestHandler):
  def get(self):

    requestedType = self.request.get('Type', 'File')
    type='Sales'
    if (requestedType == 'Image'):
        type='File'
    file_pages=db.GqlQuery("SELECT * FROM Page WHERE type='%s' ORDER BY url "% type)
    values={'file_pages': file_pages}
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'fck_connector_FilesAndFolders.xml')
    self.response.out.write(template.render(path, values))  
class AdminHandler(EasywebRequestHandler):
  def setup_thanks_page(self):
      thanks_pages=db.GqlQuery("SELECT * FROM Page WHERE type='Thanks' ORDER BY url ")
      if (thanks_pages.count() < 1):
          url = "/thanks/"
          type = "Thanks"
          page=self.get_page_for_write(url, type=type)
          page.title = "Thanks"
          page.html = "<h1>Thanks</h1>"
          page.editor = "inplace"
          page.include_in_sitemap = False
          page.put()
  def get(self):
    self.setup_thanks_page()
    template_name = 'admin.html'
    url=self.request.path
    match = re.match("/admin/(.*)$", url)
    if match:
        my_file=match.groups()[0]
        logging.debug ("template: %s" % my_file)
        if my_file:
            template_name=my_file
    sales_pages=db.GqlQuery("SELECT * FROM Page WHERE type='Sales' ORDER BY url ")
    thanks_pages=db.GqlQuery("SELECT * FROM Page WHERE type='Thanks' ORDER BY url ")
    file_pages=db.GqlQuery("SELECT * FROM Page WHERE type='File' ORDER BY url ")
    products=db.GqlQuery("SELECT * FROM Product ORDER BY name")
    payments=db.GqlQuery("SELECT * FROM Payment ORDER BY creation_date")
    values = {
              'sales_pages' : sales_pages,
              'thanks_pages' : thanks_pages,
              'file_pages' : file_pages,
              'products' : products,
              'payments' : payments,
              'preferences' : self.get_preferences(),
              'logout_url': users.create_logout_url("/"),
              'template_name': template_name,
              'domain': self.get_domain(),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', template_name)
    self.response.out.write(template.render(path, values))

class TemplateHandler(EasywebRequestHandler):
  def get(self):
#    url = self.request.url
#    pos = url.find('/', 9) # find the first / after the http:// part
#    domian= url[:pos]
    products=db.GqlQuery("SELECT * FROM Product ORDER BY name")
    values = {
              'domain' :self.get_domain(),
              'products' : products,
              'preferences' : self.get_preferences(),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'fcktemplate.xml')
    self.response.out.write(template.render(path, values))
class SitemapHandler(EasywebRequestHandler):
  def get(self):
    pages=db.GqlQuery("SELECT * FROM Page where include_in_sitemap = True ORDER BY url")
    values = {
              'pages' : pages,
              'domain' :self.get_domain(),
              }
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'sitemap.xml')
    self.response.out.write(template.render(path, values))

class SaveHandler(EasywebRequestHandler):
    def process_mht_file(self, content, file_url, promote, type, pageWidth=0):
        logging.info("process mht_file")
        msg = email.message_from_string(content)
        file_path = file_url
        if not file_url.endswith("/"):
            pathloc= file_url.rfind("/")
            file_path=file_url[:pathloc+1]
        for part in msg.walk():
            ct = part.get_content_type()
            logging.info("process mht_file: part (%s)" %(ct))
            if (ct.startswith("text/html") or ct.startswith("image")):
                regex = re.compile("file:///[A-Z]:/[a-zA-Z0-9]*/")
                file_name = regex.sub( file_path , part.get('Content-Location'))
                content = part.get_payload(decode=True)
                title="Uploaded File"
                promote_file=False
                file_type="File"
                style_key=""
                #if (ct.startswith("text/html")):
                if file_name.find("_files")==-1:
                    content = regex.sub( file_path , content)
                    if pageWidth:
                        body_style="<style>body {width:%ipx;margin-left:auto;margin-right:auto;}</style>"%pageWidth
                        end_body_loc = content.rfind('</head')
                        content="%s%s%s" % (content[:end_body_loc], body_style, content[end_body_loc:])            
                    html_soup =  BeautifulSoup(content)
                    logging.info("soup: %s" % html_soup.html.head.title)
                    title_match=html_soup.head.title
                    if title_match:
                        title=str(title_match.string)
                    promote_file=promote
                    file_name = file_path
                    file_type=type
                page = self.get_page_for_write(file_name)
                page.url = file_name
                page.html = content
                page.title = title
                page.editor = 'Upload'
                page.include_in_sitemap = promote_file
                page.type=file_type
                page.put()
                logging.info("url: %s type: %s" %(page.url, part.get_content_type()))

    def post(self):
        logging.info("Save: post")
        key_name = self.request.get('key')
        url = self.request.get('url')
        type = self.request.get('type', 'Sales')
        editor=self.request.get('editor', 'upload')
        promote = (self.request.get('include_in_sitemap', 'false') == 'true')
        if editor=="upload":
            content=self.request.get("content")
            self.process_mht_file(content, url, promote, type)
        elif editor=="file":
            content=self.request.get("content")
            page = self.get_page_for_write(url, type='File')
            page.url = url
            page.html = content
            page.title = "Uploaded file"
            page.editor = 'Upload'
            page.include_in_sitemap = promote
            page.type='File'
            page.put()
            logging.info("url: %s type: %s" %(page.url, page.type))

        else:
            page=self.get_page_for_write(url, type=type)
            if (key_name):
                logging.info("Save with key")
                page= db.get(db.Key(key_name))
            logging.info("Save: editor: %s" %(editor))
            page.url = url
            page.title = self.request.get('title')
            page.editor = self.request.get('editor')
            page.html = self.getBody(str(self.request.get('html')), page.title)
            page.include_in_sitemap = promote
            page.put()
        self.redirect('/admin/pages.html')
    def getBody(self, html_body, html_title):
        values = {
                  'html_title': html_title,
                  'html_body': html_body,
                  'domain': self.get_domain(),
                  }
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'standard_content.html')
        return template.render(path, values)
class UploadHandler(EasywebRequestHandler):

    def post(self):
        logging.info("**** upload handler called ** exiting")
        self.response.out.write("**** upload handler called ** exiting")

    def xpost(self):
        file_url=self.request.get("file_url")        
        file_name=self.request.get("file_name")
        content=self.request.get("content")
        logging.info("upload:" + file_name)
        
        lower_file_name = file_name.lower()
        if (lower_file_name.endswith(".mht") or lower_file_name.endswith(".mhtml") ):
            self.process_mht_file(content, file_url)
        else:
            page = self.get_page_for_write(file_url)
            page.url = file_url
            page.html = content
            page.title = "test"
            page.include_n_sitemap = False
            page.put()
            

        self.redirect('/admin/pages.html')    

class PreferencesHandler(EasywebRequestHandler):
  def post(self):
      logging.info("save preferences:")
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

class ProductHandler(EasywebRequestHandler):
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
class EditFileHandler(EasywebRequestHandler):
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
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit_file.html')
    self.response.out.write(template.render(path, values))
class EditProductHandler(EasywebRequestHandler):
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

class EditHandler(EasywebRequestHandler):
  def get(self):
    key_name = self.request.get('key')
    url = self.request.get('url')
    type = self.request.get('type', 'Sales')
    page={ 'type' : type }
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

class AdminRedirector(EasywebRequestHandler):
    def post(self):
        self.get()
    def get(self):
        self.redirect('/admin/pages.html')

############################################        
class PaypalIPNHandler(EasywebRequestHandler):
    live_url = "https://www.paypal.com/cgi-bin/webscr"
    test_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'

    def post(self):
        self.get()
    def get(self):
        self.process_ipn(1)
        self.response.out.write('ipn processing complete')

    def process_ipn(self, do_paypal_verification):
        preference_list=db.GqlQuery("SELECT * FROM Preferences LIMIT 1")
        preferences = preference_list.get()

        data = {}
        for i in self.request.arguments():
            data[i] = self.request.get(i)

        product_key = self.request.get('custom')
        logging.info("key = " + product_key)
        product = db.get(db.Key(product_key))

        ipn_verified = True
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
           
        template_values = {
            'payment'     : payment,
            'product'     : product,
            'ipn_verified': ipn_verified,
            'price_verified': price_verified,
            'variables'   : dict_to_string(data),
            'domain'      : self.get_domain(),
        }

        subject=''
        body=''
        sender = preferences.admin_email
        to = preferences.admin_email
        #link_token = '<img alt="Insert_Link_Here" src="/static/admin/images/insert_link_here.png" />'
        link= "%s/download/%s/%s" %( self.get_domain(), payment.key(), product.file_name)
        if verified:
            # send email to user
            subject = product.sucess_email_subject
            body_soup = BeautifulSoup(product.sucess_email_body)
            link_markers = body_soup.findAll('img', {'alt' : 'Insert_Link_Here'})
            for marker in link_markers:
                marker.replaceWith(link)
            body = "%s" % body_soup
            to = payment.payer_email
        else:
            # send email to admin
            subject = "Verification Failure"
            path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'purchase_validation_error_email.html')
            body = template.render(path, template_values)
        if do_paypal_verification:            
            message = mail.EmailMessage(sender=sender, subject=subject, to=to, body=body )
            message.send()
        else:
            logging.warning("Paypal Verification dissabled: Email Message not sent. body:")
            logging.warning(body)
        return body

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


############################################
class FakePaymentHandler(PaypalIPNHandler):
    def post(self):
        body = self.process_ipn(0)
        template_values = {
            'body'      : body,
        }        
        path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'fake_payment.html')
        self.response.out.write(template.render(path, template_values))
        #self.redirect('/admin/purchases.html')
    
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
                                        ('/admin/newProduct/', EditProductHandler),
                                        ('/admin/newFile/', EditFileHandler),
                                        ('/admin/editProduct/', EditProductHandler),
                                        ('/admin/savePayment/', FakePaymentHandler),
                                        ('/admin/new/', EditHandler),
                                        ('/admin/edit/', EditHandler),
                                        ('/download/.*', DownloadHandler),
                                        ('/Sitemap.xml', SitemapHandler),
                                        ('/fcktemplate.xml', TemplateHandler),
                                        ('/myCKtemplates.js', TemplateHandler),
                                        ('/purchase/ipn/', PaypalIPNHandler),
                                        ('/admin/upload/', UploadHandler),
                                        ('/product/.*', UserProductHandler),
                                        ('/style/.*', StyleHandler),
                                        ('/connector.py', FckConnectorHandler),
                                        ('.*', MainHandler),
                                        ])
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
