
$(document).ready(function(){
	$(".paste").validate({
		rules: {
			paste: {
				required: true
			}
		},
		messages: {
			paste: {
				required: _("This field is required")
			}
		}
	});
	$(".upload").validate({
		rules: {
			upload: {
				required: true,
				extension: "txt|docx|rtf",
			}
		},
		messages: {
			upload: {
				required: _("This field is required")
				extension: _("Only these file types are accepted: txt, docx, rtf")
			}
		}
	});
});