var data = ""
var points = []


function save_data() {
  data = "";
  points = [];
  $('tbody').children('tr').each(function() {
    let xp = parseFloat($($($(this).children()).children()[0]).val());
    let yp = parseFloat($($($(this).children()).children()[1]).val());
    let heading = parseFloat($($($(this).children()).children()[2]).val());
    if (isNaN(heading)) {
      heading = 0;
    }
    if (isNaN(xp)) {
      xp = 0;
    }
    if (isNaN(yp)) {
      yp = 0;
    }
    let reverse = ($($($(this).children()).children()[5]).prop('checked'));
    data += xp + "," + yp + "," + heading + ";";
    points.push({x: xp, y: yp});
    //$('#points').append("<tr class='point move-cursor'><td>"+xp+","+yp+"</td></tr>");
    });

}

function load_data(){

}

function update_graph() {

aaa= [{x: 4, y: 5}];
save_data();
var chart = new CanvasJS.Chart("chart-container", {
  //animationEnabled: true,
  backgroundColor: "transparent",
  axisY:{
       title: "",
       minimum: 0,
       maximum: 8,
       tickLength: 0,
       lineThickness:0,
       gridThickness: 0,
       margin:-10,
       valueFormatString:" " //comment this to show numeric values
      },
  axisX:{
       title: "",
       minimum: 0,
       maximum: 16,
       tickLength: 0,
       lineThickness:0,
       margin:-10,
       gridThickness: 0,
       valueFormatString:" " //comment this to show numeric values
      },
  toolTip:{
       cornerRadius: 4,
       enabled: falses,
      },
  data: [
    {color: "black",
    type: "spline",
    highlightEnabled: true,
    markerSize: 0,
    name: "Spline",
    showInLegend: false,
    dataPoints: points
  },
    {color: "white",
    type: "scatter",
    fillOpacity: 0.5,
    toolTipContent: "x: {x}, y: {y} ",
    //toolTipContent: "<span style='color:#4F81BC '><b>{name}</b></span><br/><b> Load:</b> {x} TPS<br/><b> Response Time:</b></span> {y} ms",
    name: "points",
    showInLegend: false,
    highlightEnabled: true,
    dataPoints: points
  }]
});
chart.render(); }
window.onload = update_graph();

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='update_graph()'></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='update_graph()'></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='update_graph()'></td>"+
    "<td class='reverse'><label class='toggle'><input type='checkbox' value='true' checked><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
}

function delete_point (elem) {
  $(elem).parent().parent().remove();
  update_graph();
}

function solve() {
  var points_elements = document.getElementsByClassName("point");
  var points = [];
  for (var i = 0; i < points_elements.length; i++) {
    var point = {};
    point["x"] = Number(points_elements[i].querySelectorAll('.x > input')[0].value);
    point["y"] = Number(points_elements[i].querySelectorAll('.y > input')[0].value);
    point["heading"] = Number(points_elements[i].querySelectorAll('.heading > input')[0].value);
    point["reverse"] = points_elements[i].querySelectorAll('.reverse > input:checked').value;
    points.push(point);
  }
  var params = {}
  params["poly"] = Number(document.getElementById("polinum").value);
  params["pos"] = Number(document.getElementById("position").value);
  params["angle"] = Number(document.getElementById("angle").value);
  params["radius"] = Number(document.getElementById("radius").value);
  params["radius_cont"] = Number(document.getElementById("radius_cont").value);
  params["length"] = Number(document.getElementById("length").value);

  var data = {"params": params, "points":points}
  var data = JSON.stringify(data);
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status){console.log(data)});
}