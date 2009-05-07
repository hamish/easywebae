from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os;

class MainPage1(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write('Hello, 1!')

class MainPage2(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write('Hello, 2!')

application1 = webapp.WSGIApplication(
                                     [('.*', MainPage1)],
                                     debug=True)

application2 = webapp.WSGIApplication(
                                     [('.*', MainPage2)],
                                     debug=True)

localdomains = ('localhost')
def main():
    server_name = os.environ.get('SERVER_NAME')
    if server_name in localdomains:
        run_wsgi_app(application1)
    else:        
        run_wsgi_app(application2)
        
if __name__ == "__main__":
  main()