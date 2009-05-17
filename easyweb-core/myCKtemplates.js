/*
Copyright (c) 2003-2009, CKSource - Frederico Knabben. All rights reserved.
For licensing, see LICENSE.html or http://ckeditor.com/license
*/

// Register a templates definition set named "default".
CKEDITOR.addTemplates( 'default',
{
	// The name of sub folder which hold the shortcut preview images of the
	// templates.
	imagesPath : CKEDITOR.getUrl( '/static/admin/images/' ),

	// The templates definitions.
	templates :
		[
  {% if not preferences.admin_email %}
			{
				title: 'Admin Email not set',
				image: 'template1.gif',
				description: 'The Administrator email must be set in the website preferences before the buy now buttons are available',
				html:
					'<p>Admin email Id not set</p>'
			},
  {% endif %}
  
  {% if not preferences.paypal_id and not preferences.paypal_sandbox_id %}
  			{
				title: 'Paypal ID not set',
				image: 'template1.gif',
				description: 'The Paypal Id must be set in the website preferences before the buy now buttons are available',
				html:
					'<p>Paypal Id not set</p>'
			},
  {% endif %}
  
{% for product in products %}
  {% if preferences.paypal_id and preferences.admin_email %}
  			{
				title: 'Buy Now Button',
				image: 'buynow.gif',
				description: 'Buy now button for {{product.name}} (${{product.price}})',
				html:
					'<form action="https://www.paypal.com/cgi-bin/webscr" method="post">'+
					'<input type="hidden" name="business" value="{{preferences.paypal_id}}">'+
					{% include "cktemplate_common_values.js" %}
					'<br />'+
					'</form>'					
			},
  {% endif %}

  {% if preferences.paypal_sandbox_id and preferences.admin_email %}
    			{
				title: 'Buy Now Button (Developers Sandbox)',
				image: 'buynow.gif',
				description: 'Sandbox Buy now button for {{product.name}} (${{product.price}})',
				html:
					""+<r><![CDATA[
						<form action="https://www.sandbox.paypal.com/cgi-bin/webscr" method="post">
						<input type="hidden" name="business" value="{{preferences.paypal_sandbox_id}}">
						{% include "cktemplate_common_values.js" %}
						<br />(Sandbox)
						</form>	
					]]></r>;								
			},
  {% endif %}
{% endfor %}

  			{
				title: 'insert link here',
				image: 'insert_link_here.gif',
				description: 'Insert Link there',
				html:
					'<img src="/static/admin/images/insert_link_here.png" />'
			},
		]
});
