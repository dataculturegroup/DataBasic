
$(document).ready(function(){

	var maxFileSize;

	if( typeof $('#max-file-size-in-mb').data() !== 'undefined' ) {
		maxFileSize = $('#max-file-size-in-mb').data().value;
	} 

	jQuery.validator.addMethod("custom_url", function(value, element) {
		return this.optional (element) || /^[^ "]+$/.test(value);
	}, _("You must input a valid url"));

	jQuery.validator.addClassRules({
		custom_url: { custom_url: true }
	});

	jQuery.validator.addMethod("multiple_files", function(value, element) {
		return this.optional (element) || $("input:file")[0].files.length == 2;
	}, _("You must select two files"));

	jQuery.validator.addMethod("filesize", function(value, element, filesize) {
		return this.optional (element) || (element.files[0].size / 1048576 <= filesize);
	});

	jQuery.validator.addClassRules({
		multiple_files: { multiple_files: true }
	});

	$(".sample").validate({
		rules: {
			sample: {
				required: true
			},
			sample2: {
				required: true
			},
			email: {
				required: true,
				email: true
			}
		},
		messages: {
			sample: {
				required: _("This field is required")
			},
			sample2: {
				required: _("This field is required")
			},
			email: {
				required: _("This field is required"),
				email: _("Please enter a valid email address")
			}
		}
	})
	$(".upload").validate({
		rules: {
			upload: {
				required: true,
				extension: "txt|docx|rtf",
				filesize: maxFileSize
			},
			upload2: {
				required: true,
				extension: "txt|docx|rtf",
				filesize: maxFileSize
			},
			email: {
				required: true,
				email: true
			}
		},
		messages: {
			upload: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf"),
				filesize: _("Only files under " + maxFileSize + "MB are accepted")
			},
			upload2: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf"),
				filesize: _("Only files under " + maxFileSize + "MB are accepted")
			},
			email: {
				required: _("This field is required"),
				email: _("Please enter a valid email address")
			}
		}
	});
});