from selenium import selenium
import unittest, time, re

global form, url_field, html_field, save_button, editor_locator
form = "//form[@name='newRecord']"
url_field = form + "//input[@name='url']"
html_field = form + "//textarea[@name='html']"
save_button = form + "//input[@name='Save']"

# This is the div used by nice edit for data entry
#editor_locator = "//div[@id='html_entry']/div[2]/div"
#editor_locator = "//iframe[@id='html_editor']/html/body"
editor_locator = "//html/body"

class NewTest(unittest.TestCase):

    def setRichTextContent(self, sel, body):
        html_data = "<body>" + body + "</body>"
        sel.run_script("myEditor.setEditorHTML(" + html_data + ");")


    def get_time(self):
        return "%.0f" % (time.time() * 10000)


    def create_new_record(self, sel, current_time, body):
        time.sleep(2)
        #Enter data for a new record       
        sel.type(url_field, "/test_" + current_time)
        
        #body = "MY Test[" + current_time + "]"
        #html_data = "<html>\n<head>\n<title>Create Test</title>\n</head>\n<body>\n" + body + "\n</body>\n</html>"
        self.setRichTextContent(sel, body)
#        sel.select_frame("index=0")
#        sel.focus(editor_locator)
#        sel.type_keys(editor_locator,body )
#        sel.select_frame("index=top")
        
        sel.click(save_button)
        sel.wait_for_page_to_load("30000")
    
    def assertNewRecordForm(self, sel):        
        #verify that the for to enter a new record is there.
        self.failUnless(sel.is_element_present(form))
        self.failUnless(sel.is_element_present(url_field))
        self.failUnless(sel.is_element_present(html_field))
        self.failUnless(sel.is_element_present(save_button))

##### Tests below
    def setUp(self):
        self.verificationErrors = []
        #self.selenium = selenium("localhost", 4444, "*custom /usr/lib/firefox-3.0.5/firefox -p selenium -no-remote", "http://localhost:8080/")
        self.selenium = selenium("localhost", 4444, "*custom firefox -p selenium -no-remote", "http://localhost:8080/")
        self.selenium.start()

    def test_edit_record(self):
        sel = self.selenium
        current_time = self.get_time()

        sel.open("/admin")
        #test_html_content = "<html>\n<head>\n<title>Update Test</title>\n</head>\n<body>\nMY Test[" + current_time + "]\n</body>\n</html>"
        body = "MY Test[" + current_time + "]"
        self.create_new_record(sel, current_time, body)
        
        update_link="//a[@id='url_/test_" + current_time + "']"
        self.failUnless(sel.is_element_present(update_link))

        sel.click("url_/test_" + current_time)
        sel.wait_for_page_to_load("30000")
                
        update_form = "//form[@name='url_/test_" + current_time + "']"
        update_url_field = update_form + "/input[@name='url']"
        update_html_field = update_form + "/textarea[@name='html']"
        update_save_button = update_form + "/input[@name='Save']"  
        
        self.failUnless(sel.is_element_present(update_form))

        sel.type(update_url_field, "/test_" + current_time + "_updated")
        
        body= "MY Test[" + current_time + "] updated"
        #sel.run_script("myEditor.setEditorHTML("+body+");")
        self.setRichTextContent(sel, body)
        #text_locator = "//form/div[2]/div"
#        sel.focus(editor_locator)
#        sel.key_press_native(35)
#        sel.type_keys(editor_locator, " updated" )
                
        sel.click(update_save_button)
        sel.wait_for_page_to_load("30000")    
    
        # go to the old URL - should give the standard error message
        sel.open("/test_" + current_time)
        sel.wait_for_page_to_load("30000")
        self.assertEqual(sel.get_body_text(), "nothing here")

        # go to the new URL - should give the new content.
        sel.open("/test_" + current_time + "_updated")
        sel.wait_for_page_to_load("30000")
        
        #validate the values present.
        #self.assertEqual(sel.get_title(), "Update Test - Updated")
        self.assertEqual(sel.get_body_text(), "MY Test["+ current_time +"] updated")
        self.failUnless(sel.is_text_present("MY Test["+ current_time +"] updated"))
        
    def test_simple_insert(self):
        sel = self.selenium
        #current_time = "%f" % time.time()
        current_time = self.get_time()
        sel.open("/admin")
        
        body_text= "MY Test["+ current_time +"]"
        self.assertNewRecordForm(sel)
        test_html_content = "<html>\n<head>\n<title>Create Test</title>\n</head>\n<body>\n" + body_text + "\n</body>\n</html>"
        self.create_new_record(sel, current_time, test_html_content)
        #self.create_new_record(sel, current_time, body_text)
        
        # re-validate that the new filed form is present.
        self.assertNewRecordForm(sel)
        
        update_link="//a[@id='url_/test_" + current_time + "']"
        self.failUnless(sel.is_element_present(update_link))

        sel.click("url_/test_" + current_time)
        sel.wait_for_page_to_load("30000")
        
        # validate that the expected form is in place
        entered_url_field = "//input[@value='/test_%s']" % current_time
        self.failUnless(sel.is_element_present(entered_url_field))
        #entered_html_field = "//textarea[@value='%s'" % test_html_content
        
        # go to the URL specified 
        sel.open("/test_" + current_time)
        sel.wait_for_page_to_load("30000")
        
        #validate the values present.
        #self.assertEqual(sel.get_title(), "Create Test")
        self.assertEqual(sel.get_body_text(), body_text)
        self.failUnless(sel.is_text_present(body_text))
    
    def tearDown(self):
        self.selenium.stop()



if __name__ == "__main__":
    unittest.main()
