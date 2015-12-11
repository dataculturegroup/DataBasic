
$(document).ready(function(){

	jQuery.validator.addMethod("custom_url", function(value, element) {
		return this.optional (element) || /^[^ "]+$/.test(value);
	}, _("You must input a valid url"));

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
				custom_url: true
			}
		},
		messages: {
			link: {
				required: _("This field is required"),
				custom_url: _("You must input a URL")
			}
		}
	});
});