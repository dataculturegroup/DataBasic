
$(document).ready(function(){
	
	jQuery.validator.addMethod("spreadsheet", function(value, element) {
		return this.optional (element) || /^https:\/\/docs.google.com\/spreadsheets/.test(value);
	}, _("Link must be a valid Google Spreadsheet"));

	jQuery.validator.addClassRules({
		spreadsheet: { spreadsheet: true }
	});
	
	$(".upload").validate({
	    rules: {
	    	upload: {
	      		required: true,
	          	extension: "csv|xlsx|xls"
	        }
	    },
	    messages: {
	    	upload: {
	    		required: _("This field is required"),
	    		extension: _("Only these file types are accepted: csv, xls, xlsx")
	    	}
	    }
	});
	$(".link").validate({
		rules: {
			link: {
				required: true,
				url: true,
				spreadsheet: true
			}
		},
		messages: {
			link: {
				required: _("This field is required"),
				url: _("You must input a URL")
			}
		}
	});
});