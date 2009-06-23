from selenium import selenium
import unittest, time, re, sys

class EasywebTests(unittest.TestCase):
    """
      TODO: 
        Test for sitemap
    """
        
    def setUp(self):
        self.selenium = selenium("localhost", 4444, "*chrome", "http://localhost:8080/")
        self.selenium.start()

    def tearDown(self):
        time.sleep(2)
        self.selenium.stop()

    def test_sitemap(self):
        sel = self.selenium
        current_time = self.get_time()

        self.login(sel)
        
        url_included = "/test_sitemap_included_%s" % current_time
        title = "Sitemap test %s" % current_time
        body = "Body content for [%s]." % current_time
        self.create_new_page(sel, url_included, title, body, 1)

        url_excluded = "/test_sitemap__not_included_%s" % current_time
        self.create_new_page(sel, url_excluded, title, body, 0)


        self.click_and_wait(sel, "link=External Tools")
        self.click_and_wait(sel, "id=sitemap")
        self.assert_src_contains_element(sel, url_included)
        self.assert_src_does_not_contain_element(sel, url_excluded)

    def test_anylitics_id(self):
        sel=self.selenium
        current_time = self.get_time()
        
        self.login(sel)
        
        self.set_anylitics_id(sel, "")

        url = "/test_%s" % current_time
        title = "Title For Page %s" % current_time
        body = "Body content for [%s]." % current_time
        self.create_new_page(sel, url, title, body)
        
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present(body))

        marker = '_gat._getTracker("'
        self.assert_src_does_not_contain_element(sel, marker)        
        
        anylitics_id="UA-4796991-1"
        self.set_anylitics_id(sel, anylitics_id)


        # Admin user logged in - tracking should not be present, edit link should
        edit_link = "//a[@id='edit']"
        self.open_and_wait(sel, url)
        self.assert_src_does_not_contain_element(sel, marker)        
        self.failUnless(sel.is_element_present(edit_link))
        
        
        # Admin user not logged in - tracking should be present, edit link should not
        self.logout(sel)
        self.open_and_wait(sel, url)
        self.assert_src_contains_element(sel, marker+anylitics_id)
        self.failIf(sel.is_element_present(edit_link))
   

        
    def test_create_and_update(self):
        sel = self.selenium
        current_time = self.get_time()

        url="/test_%s" % current_time
        title="Title For Page %s" %current_time
        body="Body content for [%s]." %current_time

        self.login(sel)
        self.create_new_page(sel, url, title, body)
        # Verify that the url works while logged in.
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present(body))


        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present(body))

        #Edit the page
        new_url=url+"_updated"
        new_title = title + " updated"
        new_body = "Updated content for [%s]." % current_time
        self.upadate_page(sel, url, new_url, new_title, new_body)

        # Test the old URL - Should return an error
        self.assert_error_page(sel, url)
        # assert that the error page has a link to create the page (if user is logged in as an admin)
        create_link = "//a[@id='create']"
        self.failUnless(sel.is_element_present(create_link))

        # Try again after logging out - assert that the create link is not present.
        self.logout(sel)
        self.assert_error_page(sel, url)
        self.failIf(sel.is_element_present(create_link))
        
        
        # Test the updated url. Should contain the new content and not the old content.
        self.open_and_wait(sel, new_url)
        self.failUnless(sel.is_text_present(new_body))
        self.failIf(sel.is_text_present(body))

    def test_Payment(self):
        sel=self.selenium
        current_time = self.get_time()
        file_path = "%s/tests/Sample_ebook.pdf" %sys.path[0]
        self.login(sel)
        
        self.set_anylitics_id(sel, "Fake")

        #Create a new product
        self.click_and_wait(sel, "link=Ebook")
        self.click_and_wait(sel, "//td[@onclick='document.location=\"/admin/newProduct/\"']")
        
        sel.type("product_name", "test_book_%s" %current_time)
        sel.type("product_price", "1.00")
        # todo - change this to be part of the checkout
        sel.type("product_file_upload", file_path)
        sel.select("product_return_url", "label=/thanks/")
        self.click_and_wait(sel, "//option[@value='/thanks/']")
        sel.type("sucess_email_subject", "email subject [%s]" % current_time)
        emailBody = 'Thanks for the purchase. URL:<img src="/static/admin/images/insert_link_here.png" alt="Insert_Link_Here" /> Test User '
        self.setRichTextContent(sel, emailBody, "rich_text")

        self.click_and_wait(sel, "//td[@name='submit']")

        self.open_and_wait(sel, "/admin/admin.html")
        
        sel.type("first_name", "First")
        sel.type("last_name", "Last")
        sel.type("payer_email", "blah@blah.com")
        sel.type("mc_gross", "1.00")
        sel.select("paypal_verification", "label=Success")        
        sel.select("custom", "label=test_book_%s ($1.00)" %current_time)
   
        self.click_and_wait(sel, "//input[@type='submit']")

        self.assert_src_does_not_contain_element(sel, "There was an error with the purchase")
        self.failIf(sel.is_element_present("//img[@alt='Insert_Link_Here']"))
        self.assert_src_contains_element(sel, "The following email would have been sent to the user specified")
        self.assert_src_contains_element(sel, "Thanks for the purchase.")

################# Utility Methods
    def set_page_values_and_submit(self, sel, url, title, body, sitemap):
        # Give the rich text editor some time to load 
        # This appears to only be needed some of the time. Hamish
        time.sleep(2)                
        self.validate_and_type(sel, "//form[@name='page_content']//input[@name='url']", url)
        self.validate_and_type(sel, "//form[@name='page_content']//input[@name='title']", title)
        if (sitemap):
            sel.check("include_in_sitemap")
        else:
            sel.uncheck("include_in_sitemap")
        self.setRichTextContent(sel, body)
        sel.focus("//form[@name='page_content']//input[@name='url']")
        #self.click_and_wait(sel, "//form[@name='page_content']//td[@id='save']")
        self.click_and_wait(sel, "save")

    def assert_error_page(self, sel, url):
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present("The URL was not found"))

    def upadate_page(self, sel, old_url, new_url, new_title, new_body, sitemap=0):
        self.open_and_wait(sel, "/admin/")
        self.click_and_wait(sel, "edit_" + old_url)
        self.set_page_values_and_submit(sel, new_url, new_title, new_body, sitemap)

    def create_new_page(self, sel, url, title, body, sitemap=0):
        self.open_and_wait(sel, "/admin/pages.html")
        self.click_and_wait(sel, "//td[@id='new_page_link']")
        #self.click_and_wait(sel, "link=add a new page")

        # select inplace editing
        sel.select("editor", "label=Edit online")
        sel.click("//option[@value='inplace']")
        
        self.set_page_values_and_submit(sel, url, title, body, sitemap)

    def login(self, sel):
        self.open_and_wait(sel, "/admin/")
        sel.click("admin")
        self.click_and_wait(sel, "submit-login")

    def logout(self, sel):
        self.open_and_wait(sel, "/admin/")
        self.click_and_wait(sel, "logout")

    def set_anylitics_id(self, sel, anylitics_id):
        self.open_and_wait(sel, "/admin/preferences.html")
        sel.type("anylitics_id", anylitics_id)
        sel.type("admin_email", "fake@fake.fake");
        sel.type("paypal_id", "fake@fake.fake");
        self.click_and_wait(sel,"//td[@id='save']")


    def open_and_wait(self, sel, url):
        sel.open(url)
        sel.wait_for_page_to_load("30000")
    
    def setRichTextContent(self, sel, body, fieldName='rich_text'):
        html_data = "<body>" + body + "</body>"
        script = "var oEditor = FCKeditorAPI.GetInstance('"+fieldName+"'); oEditor.SetHTML(" + html_data + ");"
        sel.run_script(script)
        
    def get_time(self):
        return "%.0f" % (time.time() * 10000)
                         
    def validate_and_type(self, sel, locator, value):
        self.failUnless(sel.is_element_present(locator))
        sel.type(locator, value)

    def click_and_wait(self, sel, locator):
        sel.click(locator)
        sel.wait_for_page_to_load("30000")

    def assert_src_contains_element(self, sel, marker):
        src = sel.get_html_source()
        self.failIf(src.find(marker)==-1)
    
    def assert_src_does_not_contain_element(self, sel, marker):
        src = sel.get_html_source()
        self.failIf(src.find(marker)!=-1)

if __name__ == "__main__":
    unittest.main()