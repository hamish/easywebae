function SplitFile()
{
    var file = document.getElementById("product_file_upload").value;
    file = file.replace(/\\/g, "/");
    var parts = file.split("/");
    var filename = parts[parts.length - 1];
    
    var bits = filename.split(".");
    var ext = bits[bits.length - 1];
    
    document.getElementById("product_file_name").value = filename;    
    document.getElementById("product_file_ext").value = ext.toLowerCase();
}

dojo.addOnLoad(function() {
    dojo.byId("topsplash").innerHTML = document.domain;

    // get url minus "http://"
    url = document.URL.substring(7, document.URL.length);
    var currentPage = url.substring(url.indexOf("/"), url.length);
    
    var menuTabs = dojo.byId("menu").childNodes;
    
    for (i = 0; i < menuTabs.length; i++) {
    	if (menuTabs[i].nodeName == "LI") {
    		var tabChildren = menuTabs[i].childNodes;
    		
    		for (j = 0; j < tabChildren.length; j++) {
    			if (tabChildren[j].nodeName == "A") {
    				if (dojo.attr(tabChildren[j], "href") == currentPage ||
    					dojo.attr(tabChildren[j], "href") == document.URL)
    				{
    					dojo.addClass(menuTabs[i], "active");
    				}
    				else if (dojo.hasClass(menuTabs[i], "active"))
    				{
    					dojo.removeClass(menuTabs[i], "active");
    				}
    			}
    		}
    	}
    }
});
