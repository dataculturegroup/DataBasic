$(document).ready(function(){
  var maxFileSize;

  if (typeof $('#max-file-size-in-mb').data() !== 'undefined') {
    maxFileSize = $('#max-file-size-in-mb').data().value;
  }

  jQuery.validator.addMethod("filesize", function(value, element, filesize) {
    return this.optional(element) || (element.files[0].size / 1048576 <= filesize);
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
              extension: "csv|xlsx|xls",
              filesize: maxFileSize
          },
      },
      messages: {
        upload: {
          required: _("This field is required"),
          extension: _("Only these file types are accepted: csv, xls, xlsx"),
          filesize: _("Only files under " + maxFileSize + "MB are accepted")
        }
      }
  });
});