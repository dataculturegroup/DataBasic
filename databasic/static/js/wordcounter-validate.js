
$(document).ready(function(){

	var maxFileSize;

	if( typeof $('#max-file-size-in-mb').data() !== 'undefined' ) {
		maxFileSize = $('#max-file-size-in-mb').data().value;
	} 

	jQuery.validator.addMethod("custom_url", function(value, element) {
		return this.optional (element) || /^[^ "]+$/.test(value);
	}, _("You must input a valid url"));

	jQuery.validator.addMethod("filesize", function(value, element, filesize) {
		return this.optional (element) || (element.files[0].size / 1048576 <= filesize);
	});

	jQuery.validator.addClassRules({
		custom_url: { custom_url: true }
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
				extension: "txt|docx|rtf",
				filesize: maxFileSize
			}
		},
		messages: {
			upload: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf"),
				filesize: _("Only files under " + maxFileSize + "MB are accepted")
			}
		}
	});
	$(".link").validate({
		rules: {
			link: {
				required: true,
				custom_url: true,
				filesize: maxFileSize
			}
		},
		messages: {
			link: {
				required: _("This field is required"),
				custom_url: _("You must input a URL"),
				filesize: _("Only files under " + maxFileSize + "MB are accepted")
			}
		}
	});
});