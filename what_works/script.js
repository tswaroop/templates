$('.tgl_ref')
  .urlfilter({
    selector: '.chart_tgl',
    attr: 'data-ref',
    target: 'pushState'
}).on('loaded.g.urlfilter', reload_togl)

function reload_togl(){
  var params = G.url.parse(location.href).searchKey
  var png_href = G.url.parse($("li.png_ a").attr('href'))
  var png_url = G.url.parse(png_href.searchKey['url'])
  if (!params['chart_tgl']){
    params['chart_tgl']='Show'
  }
  $('.charts').removeClass('hide');
  var chrt_tgl = params['chart_tgl']
  png_url = png_url.update({'chart_tgl': chrt_tgl}).toString()
  png_href = png_href.update({'url': png_url}).toString()
  $("li.png_ a").attr('href', png_href)
    if (chrt_tgl=='Hide'){
      $('#bubble_div').hide();
      $('#client_table_div').removeClass('col-md-6')
      $('.table_cal').css('font-size','1em')
    }
    if (chrt_tgl=='Show'){
      $('#client_table_div').addClass('col-md-6');
      $('#bubble_div').show();
      $('#bub_chrt_cnvs').removeAttr('style');
      $('.table_cal').css('font-size','.86em')
    }
}

$(".chart_tgl").click(function(){
    $('.chart_tgl').removeClass('active')
    $(this).addClass('active')
    $('input[name=chart_tgl]').attr('value', $(this).attr('id'))
});

reload_togl();

$('.bubble_chart circle').each(function() {
    var title = $('title', this);
    $(this).attr('title', title.text());
    title.remove();
})
var lastsearch= ' '
$('body').on('keypress, change, keyup', '.search_word', function(){
  var search = $(this).val();
  if(lastsearch != search){
    lastsearch = search;
    var re = new RegExp(search, "i");

    $('.bubble_chart circle, .table_metric tr').each(function(d){
        var client_name = $(this).attr('data-search');
        re.test(client_name) ? $(this).removeClass('hide') : $(this).addClass('hide');
        })
  }
})
$("#Client").autocomplete({
  source: {{tot_clients.keys()}},
  change: function (event, ui) {
      $(this).val((ui.item ? ui.item.value : ""));
      if(!ui.item){
        $('#myDropdown').modal('show');
      }
  }
});
$( "#Client" ).autocomplete( "widget" ).addClass('Client');

$("#TG_Market").autocomplete({
  source: {{dumps(tg_names)}},
  change: function (event, ui) {
      $(this).val((ui.item ? ui.item.value : ""));
      if(!ui.item){
        $('#myDropdown').modal('show');
      }
  }
});
$( "#TG_Market" ).autocomplete( "widget" ).addClass('TG_Market');

$("#BG_Market").autocomplete({
  source: {{dumps(b_names)}},
  change: function (event, ui) {
      $(this).val((ui.item ? ui.item.value : ""));
      if(!ui.item){
        $('#myDropdown').modal('show');
      }
  }
});
$( "#BG_Market" ).autocomplete( "widget" ).addClass('BG_Market');

$('a.downloadCsv').on('click', function(e){
  var csv_data = {{dumps(csv_data)}}
  e.preventDefault();
  G.download({
    file: 'What_Works_Best_For_' + {{ json.dumps(client.title()) }} +'.csv',  // Save the file as ...
    csv:  csv_data// Data to download
    // You can specify the data as an array of arrays,
    // or as an array of dictionaries. For example:
    // csv: [{A:1, B:2, C:3}, {A:3, B:4, C:5}]
  })
});
$('.highlight-controls').highlight();

var intervals = {
  s : 1000,
  m : 60000,
  h : 3600000,
  d : 86400000,
  w : 604800000
}

function dateDiff(interval,date1,date2) {
  if( "smhdw".indexOf(interval) == -1 ) {
    return "error";
  }
  if( !date1 )
    return "error";

  if( !date2 )
    return "error";

  var diff = (date2 - date1) / intervals[interval];
  return diff;
}

$('.filter-buttons .btn-submit').on('click', function(event){
  date1= new Date($('.fst').val())
  date2= new Date($('.sec').val())
  weekDiff = Math.floor(dateDiff('w',date1,date2)) + 1;
  if (weekDiff>52) {
    $('#myModal').modal('show');
    $(".loading").hide();
    event.preventDefault();
  }
});
Date.prototype.getWeek = function() {
      var onejan = new Date(this.getFullYear(), 0, 1);
      var jan_day = onejan.getDay();
      if (jan_day == 0){jan_day = 7;}
      // console.log(Math.floor((((this - onejan) / 86400000) + jan_day + 1) / 7));
      return Math.floor((((this - onejan) / 86400000) + jan_day + 1) / 7);
}
function display_yr_wk(){
  frm_date = new Date($('.fst').val());
  frm_year = frm_date.getFullYear();
  frm_wek_no = frm_date.getWeek(frm_year);
  frm_dt = frm_year + '-' + frm_wek_no;
  to_date = new Date($('.sec').val());
  to_year = to_date.getFullYear();
  to_wek_no = to_date.getWeek(to_year);
  frm_dt = frm_year + '-' + frm_wek_no;
  to_dt = to_year + '-' + to_wek_no
  date_text = frm_dt + ' To ' +to_dt
  $('.date_display').removeClass('hide')
  .text(date_text);
  $('.timeperiod').attr('title', date_text);
  $('.timeperiod').attr('data-original-title', date_text);
}
$('#week-picker input').on('change', function(e){
  display_yr_wk();
});
display_yr_wk();
var x_slider = $("#Xscale_slider").slider({}).data('slider');
var y_slider = $("#Yscale_slider").slider({}).data('slider');