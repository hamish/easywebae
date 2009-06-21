{% if is_admin %}
	<hr />
	<a href="/admin/edit/?url={{url}}" id="edit">Edit</a> this page.
{% endif %}	
	{% if preferences.anylitics_id  and not is_admin %}
		<script type="text/javascript">
			var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
			document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
		</script>
		<script type="text/javascript">
			var pageTracker = _gat._getTracker("{{preferences.anylitics_id}}");
			pageTracker._trackPageview();
		</script>
	{% endif %}