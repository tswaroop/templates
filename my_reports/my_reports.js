// To display selection
$('.filter_selection').click(function(){
  var filter_selected = $(this).text();
  $(this).parent().siblings().removeClass('active')
  $(this).parent().addClass('active')
  var filter_button = $(this).parents('.dropdown.open').find('button');
  filter_button.next('.display_selection').text(filter_selected);
})

/*
// For week datepicker
function selectrow(e){
    $('.datepicker tr td.selected.active')
    .closest('tr').addClass('dRowSelected')};

$('.week-picker input').on('click', selectrow);


// endDate comes from index.html
$('.week-picker').datepicker({
    'z-index': 9999,
    'orientation': 'top',
    'endDate': '-' + endDate_diff + 'd',
    calendarWeeks: true})
    .on('changeDate', selectrow)
    .on('show', function(e) {
        var $popup = $('.datepicker');
        $popup.click(function () {
          return false; });
    });
*/
function selectrow(e){
    $('.datepicker tr td.selected.active')
    .closest('tr').addClass('dRowSelected')
  };

$('.week-picker input').hover(selectrow);

$('.week-picker').datepicker({
    format: "mm/dd/yyyy",
    calendarWeeks: true,
    weekStart: 6,
    orientation: 'top',
    'endDate': '-' + endDate_diff + 'd',
    autoclose: true})
    .on('changeDate', selectrow)
    .on('show', function(e) {
        var $popup = $('.datepicker');
        $popup.click(function () {
          return false; });
    });

$('.date-picker').datepicker({ format: "mm/dd/yyyy",
    orientation: 'top',
    'endDate': dr_todate,
    autoclose: true,
    })
    .on('show', function(e) {
        var $popup = $('.datepicker');
        $popup.click(function () {
          return false; });
    });

// For search functionality
var lastsearch= ''
var search_input = '.search_filter';
$('body').on('keypress, change, keyup', search_input, function(){
  var search = $(this).val();
  // lastsearch = search;
  // var re = new RegExp(escape(search), "i");
  $(this).parent().parent().siblings().each(function(){
    var client_name = $(this).find('[data-search]').attr('data-search')
    if(client_name){
    client_name.toLowerCase().indexOf(
        search.toLowerCase()) >= 0 ? $(this).removeClass('hide') : $(this).addClass('hide')};
  })
})

// adjust week number for calender starts sun-sat
Date.prototype.getWeek = function() {
      var onejan = new Date(this.getFullYear(), 0, 1);
      var jan_day = onejan.getDay();
      if (jan_day == 0){jan_day = 7;}
      // console.log(Math.floor((((this - onejan) / 86400000) + jan_day + 1) / 7));
      return Math.floor((((this - onejan) / 86400000) + jan_day + 1) / 7);
  }

// For getting the week keys
function week_dp_selected(tab_name){
  var pr_from_year = new Date($('.' + tab_name + '_from_week').val()).getFullYear();
  var pr_from_week = new Date($('.' + tab_name + '_from_week').val()).getWeek(pr_from_year);
  var pr_to_year = new Date($('.' + tab_name + '_to_week').val()).getFullYear();
  var pr_to_week = new Date($('.' + tab_name + '_to_week').val()).getWeek(pr_to_year);
  var weeks_selected = []
  if (pr_from_year == pr_to_year){
    for(i=pr_from_week; i<=pr_to_week; i++){
      weeks_selected.push(week_keys[i + "-" + pr_to_year])
    }
  }
  else{
    for (i=pr_from_week; i<=52; i++){
      weeks_selected.push(week_keys[i +  "-" + pr_from_year])
    }
    for(i=1; i<=pr_to_week; i++){
      weeks_selected.push(week_keys[i + "-" + pr_to_year])
    }
  }
  return weeks_selected
}
$('.week-picker input').on('change', function(e){
  date1 = new Date($(this).parent().find('.from_dt').val());
  date2 = new Date($(this).parent().find('.to_dt').val());
  frm_year = date1.getFullYear();
  to_year = date2.getFullYear();
  frm_wek_no = date1.getWeek(frm_year);
  to_wek_no = date2.getWeek(to_year);
  from_dt = frm_year + '-' +frm_wek_no;
  to_dt = to_year + '-' +to_wek_no;
  dt_disp = from_dt;
  if(to_year){dt_disp = dt_disp + ' To ' +to_dt};
  $disp = $(this).closest(".date_wk").find("p.display_selection")
  $disp.text("");
  $disp.text(dt_disp);
})
$('.date-picker input').on('change', function(e){
  from_dt = $(this).parent().find('.from_dt').val();
  to_dt = $(this).parent().find('.to_dt').val();
  res = from_dt
  if(to_dt){res = res + '</br>To</br>' + to_dt;}
  $(this).closest(".date_day")
    .find("p.display_selection")
    .html(res);
})