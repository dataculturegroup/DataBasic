
$(document).ready(function(){

	jQuery.validator.addMethod("multiple_files", function(value, element) {
		return this.optional (element) || $("input:file")[0].files.length == 2;
	}, _("You must select two files"));

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
				extension: "txt|docx|rtf"
			},
			upload2: {
				required: true,
				extension: "txt|docx|rtf"
			},
			email: {
				required: true,
				email: true
			}
		},
		messages: {
			upload: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf")
			},
			upload2: {
				required: _("This field is required"),
				extension: _("Only these file types are accepted: txt, docx, rtf")
			},
			email: {
				required: _("This field is required"),
				email: _("Please enter a valid email address")
			}
		}
	});
});