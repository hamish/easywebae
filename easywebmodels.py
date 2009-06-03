from google.appengine.ext import db

class Page(db.Model):
    url = db.StringProperty()
    title = db.StringProperty()
    #html = db.TextProperty()
    html = db.BlobProperty()
    editor = db.StringProperty()
    type = db.StringProperty(required=True, choices=set(["Sales", "Thanks", "File"]))
    include_in_sitemap = db.BooleanProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Style(db.Model):
    content = db.BlobProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Image(db.Model):
    file_name = db.StringProperty()
    content = db.BlobProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Preferences(db.Model):
    anylitics_id = db.StringProperty()
    paypal_id = db.StringProperty()
    paypal_sandbox_id = db.StringProperty()
    admin_email = db.StringProperty()

class Product(db.Model):
    name = db.StringProperty()
    price = db.StringProperty()
    return_url = db.StringProperty()
    return_cancel_url = db.StringProperty()
    file_name = db.StringProperty()
    file_ext = db.StringProperty()
    file_content = db.BlobProperty()
    sucess_email_subject = db.StringProperty()
    sucess_email_body = db.TextProperty()
    priority = db.IntegerProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now=True)

class Payment(db.Model):
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    payer_email = db.StringProperty()
    txn_id = db.StringProperty()
    item_name = db.StringProperty()
    product_key = db.StringProperty()
    mc_gross = db.StringProperty()
    verification_url = db.StringProperty()
    verification_result = db.StringProperty()
    all_values = db.TextProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)