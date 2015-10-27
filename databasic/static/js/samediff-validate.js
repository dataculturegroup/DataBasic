
$(document).ready(function(){

	jQuery.validator.addMethod("multiple_files", function(value, element) {
		return this.optional (element) || $("input:file")[0].files.length > 1;
	}, _("You must select more than one file"));

	jQuery.validator.addClassRules({
		multiple_files: { multiple_files: true }
	});

	$(".sample").validate({
		rules: {
			samples: {
				required: true,
				minlength: 2
			},
			email: {
				required: true,
				email: true
			}
		},
		messages: {
			samples: {
				required: _("This field is required"),
				minlength: _("You must select more than one option")
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
				multiple_files: true
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
			email: {
				required: _("This field is required"),
				email: _("Please enter a valid email address")
			}
		}
	});
});