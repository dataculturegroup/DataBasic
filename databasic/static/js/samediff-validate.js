
$(document).ready(function(){
	$(".upload").validate({
		rules: {
			upload: {
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
			email: {
				required: _("This field is required"),
				email: _("Please enter a valid email address")
			}
		}
	});
});