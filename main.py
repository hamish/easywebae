#!/usr/bin/env python
#
# First steps for easyweb, a content management system running on 
# appEngine.

import cgi
import os

import wsgiref.handlers


from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class MainHandler(webapp.RequestHandler):

  def get(self):
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'index.html')
    self.response.out.write(template.render(path, {}))

class EditHandler(webapp.RequestHandler):

  def get(self):
    path = os.path.join(os.path.dirname(__file__),'easyweb-core', 'edit.html')
    self.response.out.write(template.render(path, {}))

def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/admin/?', EditHandler)
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
