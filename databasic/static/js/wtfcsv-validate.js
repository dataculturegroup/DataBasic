
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
	          	extension: "csv"
	        }
	    },
	    messages: {
	    	upload: {
	    		required: _("This field is required"),
	    		extension: _("The file must be a .csv")
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