
var send_submit_event = function(toolName, source) {
  var submit = $.urlParam('submit');
  if (submit) {
    ga('send', 'event', toolName, source, 'input-tab');
    window.location.href = window.location.href.replace('?submit=true', '#');
  }
}

$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return null;
    }
    else{
       return results[1] || 0;
    }
}

$(document).ready(function() {

  // Add classes for styling checkboxes
  $("input[type='checkbox']").change(function(){
      if($(this).is(":checked")){
          $(this).parent().parent().addClass("checked-div"); 
      }else{
          $(this).parent().parent().removeClass("checked-div");  
      }
  });

  // Focus the first field when a tab is selected
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    var tabId = $(this).attr('id').replace('tab-', '');
    $('.tab-content')
        .find('#' + tabId)
        .find('.form-group:nth(1)')
        .find('.form-control:nth(0)')[0].focus ();
  });

  // Remember last pressed tab when navigating site
  var hash = window.location.hash;
  hash && $('ul.nav a[href="' + hash + '"]').tab('show');

  $('.nav-tabs a').click(function (e) {
    $(this).tab('show');
    window.location.hash = this.hash;
  });

  // Modals accessibility
  $('#video-modal').on('shown.bs.modal', function () {
    $('a').find('iframe').focus();
    $('#video-modal-btn').prop('aria-expanded', true);
  });

  $('#video-modal').on('hidden.bs.modal', function () {
    $('a').find('iframe').focus();
    $('#video-modal-btn').prop('aria-expanded', false);
  });

  $('#share-modal').on('shown.bs.modal', function () {
    $(this).find('input').focus();
    $('#share-modal-btn').prop('aria-expanded', true);
  });

  $('#share-modal').on('hidden.bs.modal', function () {
    $(this).find('input').focus();
    $('#share-modal-btn').prop('aria-expanded', false);
  });

  // Stop video when modal is closed
  $('.modal').each(function(){
      var src = $(this).find('iframe').attr('src');

      $(this).on('click', function(){

          $(this).find('iframe').attr('src', '');
          $(this).find('iframe').attr('src', src);

      });
  });
  
  handle_upload('upload');
  handle_upload('upload2');

  function handle_upload(id) {
    $('#browse-click-' + id).on('click', function () {
        $('.form-control[name="' + id + '"]').click();
        setInterval(function() {
          var label = $('.form-control[name="' + id + '"]').val();
          if (label != "") {
            $('#browse-click-' + id).html(label);
          }
        }, 1);
        return false;
    });
  }
});