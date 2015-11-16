
$(document).ready(function(){
	
	var maxFileSize = 10000000; // 10MB

	jQuery.validator.addMethod("spreadsheet", function(value, element) {
		return this.optional (element) || /^https:\/\/docs.google.com\/spreadsheets/.test(value);
	}, _("Link must be a valid Google Spreadsheet"));

	jQuery.validator.addMethod("filesize", function(value, element, filesize) {
		return this.optional (element) || (element.files[0].size <= filesize);
	});

	jQuery.validator.addClassRules({
		spreadsheet: { spreadsheet: true }
	});
	
	$(".upload").validate({
	    rules: {
	    	upload: {
	      		required: true,
	          	extension: "csv|xlsx|xls",
	          	filesize: maxFileSize
	        },
	    },
	    messages: {
	    	upload: {
	    		required: _("This field is required"),
	    		extension: _("Only these file types are accepted: csv, xls, xlsx"),
	    		filesize: _("Only files under 10MB are accepted")
	    	}
	    }
	});
	$(".link").validate({
		rules: {
			link: {
				required: true,
				url: true,
				spreadsheet: true,
				filesize: maxFileSize
			}
		},
		messages: {
			link: {
				required: _("This field is required"),
				url: _("You must input a URL"),
				filesize: _("Only files under 10MB are accepted")
			}
		}
	});
});