from selenium import selenium
import unittest, time, re
from time import time

global form, url_field, html_field, save_button
form = "//form[@name='newRecord']"
url_field = form + "/input[@name='url']"
html_field = form + "/textarea[@name='html']"
save_button = form + "/input[@name='Save']"

class NewTest(unittest.TestCase):

    def create_new_record(self, sel, current_time, test_html_content):
        #Enter data for a new record
        
        sel.type(url_field, "/test_" + current_time)
        sel.type(html_field, test_html_content)
        sel.click(save_button)
        sel.wait_for_page_to_load("30000")
        return test_html_content
    
    def assertNewRecordForm(self, sel):        
        #verify that the for to enter a new record is there.
        self.failUnless(sel.is_element_present(form))
        self.failUnless(sel.is_element_present(url_field))
        self.failUnless(sel.is_element_present(html_field))
        self.failUnless(sel.is_element_present(save_button))

##### Tests below
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*custom /usr/lib/firefox-3.0.5/firefox -p selenium -no-remote", "http://localhost:8080/")
        self.selenium.start()

    def test_edit_record(self):
        sel = self.selenium
        current_time = "%f" % time()

        sel.open("/admin")
        test_html_content = "<html>\n<head>\n<title>SAMPLE</title>\n</head>\n<body>\nMY Test[" + current_time + "]\n</body>\n</html>"
        self.create_new_record(sel, current_time, test_html_content)
        
        
    
    def test_simple_insert(self):
        sel = self.selenium
        current_time = "%f" % time()
        sel.open("/admin")
        
        self.assertNewRecordForm(sel)
        test_html_content = "<html>\n<head>\n<title>DEF</title>\n</head>\n<body>\nMY Test[" + current_time + "]\n</body>\n</html>"
        self.create_new_record(sel, current_time, test_html_content)
        
        # re-validate that the new fild form is present.
        self.assertNewRecordForm(sel)
        
        # validate that the expected form is in place
        entered_url_field = "//input[@value='/test_%s']" %current_time
        self.failUnless(sel.is_element_present(entered_url_field))
        entered_html_field = "//textarea[@value='%s'" % test_html_content
        
        # go to the URL specified 
        sel.open("/test_" + current_time)
        sel.wait_for_page_to_load("30000")
        
        #validate the values present.
        self.assertEqual(sel.get_title(), "DEF")
        self.assertEqual(sel.get_body_text(), "MY Test["+ current_time +"]")
        self.failUnless(sel.is_text_present("MY Test["+ current_time +"]"))
    
    def tearDown(self):
        self.selenium.stop()



if __name__ == "__main__":
    unittest.main()
