from selenium import selenium
import unittest, time, re

class EasywebTests(unittest.TestCase):

    def set_page_values_and_submit(self, sel, url, title, body):
        self.validate_and_type(sel, "//form[@name='page_content']//input[@name='url']", url)
        self.validate_and_type(sel, "//form[@name='page_content']//input[@name='title']", title)
        self.setRichTextContent(sel, body)
        self.click_and_wait(sel, "//form[@name='page_content']//input[@name='Save']")


    def assert_error_page(self, sel, url):
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present("The URL was not found"))

    def upadate_page(self, sel, old_url, new_url, new_title, new_body):
        self.open_and_wait(sel, "/admin/")
        self.click_and_wait(sel, "edit_" + old_url)
        
        self.set_page_values_and_submit(sel, new_url, new_title, new_body)

    def create_new_page(self, sel, url, title, body):
        self.open_and_wait(sel, "/admin/")       
        self.click_and_wait(sel, "new")
        # Give the rich text editor some time to load 
        # This appears to only be needed some of the time. Hamish
        # time.sleep(2)
        self.set_page_values_and_submit(sel, url, title, body)

    def login(self, sel):
        self.open_and_wait(sel, "/admin/")
        sel.click("admin")
        self.click_and_wait(sel, "submit-login")

    def logout(self, sel):
        self.open_and_wait(sel, "/admin/")
        self.click_and_wait(sel, "logout")

    def open_and_wait(self, sel, url):
        sel.open(url)
        sel.wait_for_page_to_load("30000")

    
    def setRichTextContent(self, sel, body):
        html_data = "<body>" + body + "</body>"
        sel.run_script("myEditor.setEditorHTML(" + html_data + ");")
        
    def get_time(self):
        return "%.0f" % (time.time() * 10000)
                         
    def validate_and_type(self, sel, locator, value):
        self.failUnless(sel.is_element_present(locator))
        sel.type(locator, value)


    def click_and_wait(self, sel, locator):
        sel.click(locator)
        sel.wait_for_page_to_load("30000")


######################################3
    def setUp(self):
        self.selenium = selenium("localhost", 4444, "*custom firefox -p selenium -no-remote", "http://localhost:8080/")
        self.selenium.start()
        # run the tests slowly so that a human can follow along. 
        # self.selenium.set_speed(500)

    def test_create_and_update(self):
        sel = self.selenium
        current_time = self.get_time()

        url="/test_%s" % current_time
        title="Title For Page %s" %current_time
        body="Body content for [%s]." %current_time

        self.login(sel)
        self.create_new_page(sel, url, title, body)
        # Verify that the url works.
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present(body))

        # Verify that the url works if you are logged out. 
        self.logout(sel)
        self.open_and_wait(sel, url)
        self.failUnless(sel.is_text_present(body))

        #Edit the page
        self.login(sel)
        new_url=url+"_updated"
        new_title = title + " updated"
        new_body = "Updated content for [%s]." % current_time
        self.upadate_page(sel, url, new_url, new_title, new_body)

        # Test the old URL - Should return an error
        self.assert_error_page(sel, url)

        # Test the updated url. Should contain the new content and not the old content.
        self.open_and_wait(sel, new_url)
        self.failUnless(sel.is_text_present(new_body))
        self.failIf(sel.is_text_present(body))

    def tearDown(self):
        self.selenium.stop()

if __name__ == "__main__":
    unittest.main()