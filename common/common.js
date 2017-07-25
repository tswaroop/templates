/* this needs to be changed as per the requirement */

function selectrow(e){
    $('.datepicker tr td.selected.active')
    .closest('tr').addClass('dRowSelected')
  };

$('#week-picker input').hover(selectrow);

$('#week-picker').datepicker({
    format: "mm/dd/yyyy",
    calendarWeeks: true,
    weekStart: 6,
    autoclose: true})
    .on('changeDate', selectrow)
    .on('show', function(e) {
        var $popup = $('.datepicker');
        $popup.click(function () {
          return false; });
    });

$("body").on('click', ".insights .title", function(e){
  $(".insights").toggleClass('clicked');
  if ($(".insights").hasClass('clicked')){
    $(".modal-backdrop").remove();
    $("body").append('<div class="modal-backdrop fade in dim_bk"></div>');
  }
  else {
    $('.dim_bk').remove()
  }
})
$("body").on('click', ".left_menu .title", function(e){
  $(".left_menu").toggleClass('clicked');
  if ($(".left_menu").hasClass('clicked')){
    $(".modal-backdrop").remove();
    $("body").append('<div class="modal-backdrop fade in dim_bk_left"></div>');
  }
  else {
    $('.dim_bk_left').remove()
  }
})

/* Function responsible for automatically timeout the session if idle for 10 seconds*/
var idleTime = 0;
$(document).ready(function () {
    //Increment the idle time counter every minute.
    var idleInterval = setInterval(timerIncrement, 200000000); // 2 minutes

    //Zero the idle timer on mouse movement.
    $(this).mousemove(function (e) {
        idleTime = 0;
    });
    $(this).keypress(function (e) {
        idleTime = 0;
    });
});

function timerIncrement() {
    idleTime = idleTime + 1;
    if (idleTime > 1) {
        var cookies = document.cookie.split(';')
        for(i=0; i< cookies.length; i++){
            setCookie(cookies[i],null,-1)
        }
	location.reload()
    }
}

function setCookie(name, value, seconds) {

    if (typeof(seconds) != 'undefined') {
        var date = new Date();
        date.setTime(date.getTime() + (seconds*1000));
        var expires = "; expires=" + date.toGMTString();
    }
    else {
        var expires = "";
    }

    document.cookie = name+"="+value+expires+"; path=/";
}

$("body").append("<div class='loading hide'></div>");

$(".btn.load").on("click", function(e){
  $('.loading').removeClass("hide");
})
/* end of cookie clear function */