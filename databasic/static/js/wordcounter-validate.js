
$(document).ready(function(){

	jQuery.validator.addMethod("complete_url", function(val, elem) {
	    // if no url, don't do anything
	    if (val.length == 0) { return true; }
	 
	    // if user has not entered http:// https:// or ftp:// assume they mean http://
	    if(!/^(https?|ftp)://i.test(val)) {
	        val = 'http://'+val; // set both the value
	        $(elem).val(val); // also update the form element
	    }
	    // now check if valid url
	    // http://docs.jquery.com/Plugins/Validation/Methods/url
	    // contributed by Scott Gonzalez: http://projects.scottsplayground.com/iri/
	    return /^(https?|ftp)://(((([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(%[da-f]{2})|[!$&amp;'()*+,;=]|:)*@)?(((d|[1-9]d|1dd|2[0-4]d|25[0-5]).(d|[1-9]d|1dd|2[0-4]d|25[0-5]).(d|[1-9]d|1dd|2[0-4]d|25[0-5]).(d|[1-9]d|1dd|2[0-4]d|25[0-5]))|((([a-z]|d|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(([a-z]|d|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])*([a-z]|d|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF]))).)+(([a-z]|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(([a-z]|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])*([a-z]|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF]))).?)(:d*)?)(/((([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(%[da-f]{2})|[!$&amp;'()*+,;=]|:|@)+(/(([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(%[da-f]{2})|[!$&amp;'()*+,;=]|:|@)*)*)?)?(?((([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(%[da-f]{2})|[!$&amp;'()*+,;=]|:|@)|[uE000-uF8FF]|/|?)*)?(#((([a-z]|d|-|.|_|~|[u00A0-uD7FFuF900-uFDCFuFDF0-uFFEF])|(%[da-f]{2})|[!$&amp;'()*+,;=]|:|@)|/|?)*)?$/i.test(val);
	});

	$(".paste").validate({
		rules: {
			area: {
				required: true
			}
		},
		messages: {
			area: {
				required: _("This field is required")
			}
		}
	});
	$(".upload").validate({
		rules: {
			upload: {
				required: true,
				extension: "txt|docx|rtf"
			}
		},
		messages: {
			upload: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf")
			}
		}
	});
	$(".link").validate({
		rules: {
			link: {
				required: true,
				// url: true
				complete_url: true
			}
		},
		messages: {
			link: {
				required: _("This field is required"),
				// url: _("You must input a URL")
				complete_url: _("You must input a URL")
			}
		}
	});
});