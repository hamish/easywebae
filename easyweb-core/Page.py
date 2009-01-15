from google.appengine.ext import db

class Page(db.Model):
    url = db.StringProperty()
    html = db.StringProperty(multiline=True)
    creation_date = db.DateTimeProperty(auto_now_add=True)
