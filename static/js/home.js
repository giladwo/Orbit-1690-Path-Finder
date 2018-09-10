//var data = "";
var ctx;
var field_img;
var field_canvas;
var pixel_meters;

const default_data = [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}]

var parsed_data  = [default_data]; //stores all the data got from python 
var data_version = 0; //stores current data version
var new_solve    = true; //whether there is data or not

var robot_width  = 0.6 //Meters 
var robot_height = 0.8 //Meters

const point_size = 5;
const path_size  = 1;

const real_field_width  = 16; //Meters
const real_field_height = 8; //Meters

function get_mouse_pos (canvas, evt) {
  var rect = canvas.getBoundingClientRect();
  return {x: evt.clientX - rect.left, y: evt.clientY - rect.top};
}

function in_range (pos0, pos1, radius) {
  if (Math.sqrt((pos0["x"]-pos1["x"])^2 + (pos0["y"]-pos1["y"])^2) < radius) {
    return true;
  } 
  return false;
}

function get_data () {
  return(parsed_data[data_version]);
}

function get_points () {
  var points_elements = document.getElementsByClassName("point");
  var points = [];
  for (var i = 0; i < points_elements.length; i++) {
    var point = {};
    point["x"] = Number(points_elements[i].querySelectorAll('.x > input')[0].value);
    point["y"] = Number(points_elements[i].querySelectorAll('.y > input')[0].value);
    point["heading"] = Number(points_elements[i].querySelectorAll('.heading > input')[0].value)*Math.PI/180;
    point["switch"] = String(points_elements[i].querySelectorAll('.switch > label > input')[0].checked);
    points.push(point);
  }
  return points
}

function draw_robot () {
  let previous = ctx.globalCompositeOperation;
  ctx.globalCompositeOperation = "destination-over";

  let translation = position.translation;

  ctx.translate(translation.drawX, translation.drawY);
  ctx.rotate(-heading);

  let w = robotWidth * (width / fieldWidth);
  let h = robotHeight * (height / fieldHeight);
  ctx.fillStyle = color || "rgba(0, 0, 0, 0)";
  ctx.fillRect(-h / 2, -w / 2, h, w);

  ctx.rotate(heading);
  ctx.translate(-translation.drawX, -translation.drawY);

  ctx.globalCompositeOperation = previous;
}

function draw_path (points){
  ctx.beginPath();
  
  var inc = 2; 
  for (var i = 0; i < points.length - inc; i+=inc){
    var val = parseInt(i*100/points.length);
    color = "rgba(200,200,200,1)";
    ctx.fillStyle = color;
    ctx.beginPath();
    
    let x = points[i]["x"];
    let y = points[i]["y"];
    let x1 = points[i+inc]["x"];
    let y1 = points[i+inc]["y"];

    let alpha = Math.atan2((y1-y),(x1-x));
    
    x = x + Math.cos(alpha)*robot_height/2;
    y = y + Math.sin(alpha)*robot_height/2;

    let xr = Math.cos(alpha+Math.PI/2)*robot_width/2 + x;
    let yr = Math.sin(alpha+Math.PI/2)*robot_width/2 + y;
    
    let xl = Math.cos(alpha-Math.PI/2)*robot_width/2 + x;
    let yl = Math.sin(alpha-Math.PI/2)*robot_width/2 + y;

    ctx.arc (xr*pixel_meters, yr*pixel_meters, path_size, 0, 2*Math.PI);
    ctx.arc (xl*pixel_meters, yl*pixel_meters, path_size, 0, 2*Math.PI);
    ctx.fill();
    
    color = "rgba(100,100,100,1)";
    ctx.fillStyle = color;

    x = points[i]["x"];
    y = points[i]["y"];
    
    x = x + Math.cos(alpha+Math.PI)*robot_height/2;
    y = y + Math.sin(alpha+Math.PI)*robot_height/2;

    xr = Math.cos(alpha+Math.PI/2)*robot_width/2 + x;
    yr = Math.sin(alpha+Math.PI/2)*robot_width/2 + y;
    
    xl = Math.cos(alpha-Math.PI/2)*robot_width/2 + x;
    yl = Math.sin(alpha-Math.PI/2)*robot_width/2 + y;

    ctx.beginPath();
    ctx.arc (xr*pixel_meters, yr*pixel_meters, path_size, 0, 2*Math.PI);
    ctx.arc (xl*pixel_meters, yl*pixel_meters, path_size, 0, 2*Math.PI);
    ctx.fill();
  }

  for (var i = 0; i < points.length; i+=inc){
    var val = parseInt(i*100/points.length);
    color = "hsl("+val+",100%,60%)";
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc (points[i]["x"]*pixel_meters, points[i]["y"]*pixel_meters, path_size, 0, 2*Math.PI);
    ctx.fill();
  }

  ctx.closePath();
}

function draw_points (points) {
  color = "#ffffff";

  for (var i = 0; i < points.length; i++){
    ctx.beginPath();
    ctx.arc (points[i]["x"]*pixel_meters, points[i]["y"]*pixel_meters, point_size, 0, 2*Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }
}

function init_field() {
  $("#loader").hide();

  field_canvas = document.getElementById("field");

  ctx = field_canvas.getContext('2d');
  field_img = new Image;
  
  field_img.onload = function() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowColor = '#101010';
    ctx.shadowBlur = 10;
    draw_points(get_points());
  };

  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
}


function draw_field() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowBlur = 0;

    for (var i = 0; i < get_data().length; i++) {
      draw_path(get_data()[i]["path_points"]);
    }
    
    document.getElementById("version-header").innerHTML = data_version + " / " + (parsed_data.length-1)
    ctx.shadowBlur = 10;
    draw_points(get_points());
}

function update_costs () {
  /* Missing here: 'for' loop to handle multiple paths costs*/
  document.getElementById("pos_cost_val").innerHTML = get_data()[0]["costs"]["pos_cost"].toPrecision(3);
  document.getElementById("angle_cost_val").innerHTML = get_data()[0]["costs"]["angle_cost"].toPrecision(3);
  document.getElementById("radius_cost_val").innerHTML = get_data()[0]["costs"]["radius_cost"].toPrecision(3);
  document.getElementById("radius_cont_cost_val").innerHTML = get_data()[0]["costs"]["radius_cont_cost"].toPrecision(3);
  document.getElementById("length_cost_val").innerHTML = get_data()[0]["costs"]["length_cost"].toPrecision(3);
}

//delete future changes and push new version of paths
function new_version (push_item) {
  if (data_version < parsed_data.length) {
      parsed_data.splice(data_version+1, parsed_data.length);
    }
  parsed_data.push(push_item);
  data_version++;
  draw_field();
}

function reset_data () {
  data_version = 0;
  parsed_data = [default_data];
  new_solve = true;
  draw_field();
}

function reset_version() {
  data_version = 0;
  draw_field();
}

function redo_change () {
  if (data_version < parsed_data.length-1) {
    data_version ++;
    draw_field();
    update_costs();
  }
}

function undo_change () {
  if (data_version > 0) {
    data_version --;
    draw_field();
    update_costs();
  }
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='reset_data()' value=1></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='reset_data()' value=1></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='reset_data()' value=0></td>"+
    "<td class='switch'><label class='toggle'><input type='checkbox' onclick='reset_data()' value='true'><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
  
  reset_data();
}

function delete_point (elem) {
  $(elem).parent().parent().remove();
  
  reset_data();
}

function solve() {
  var points = get_points();
  var params = {};
  
  params["poly"] = Number(document.getElementById("polynom").value);
  params["pos"] = Number(document.getElementById("position").value);
  params["angle"] = Number(document.getElementById("angle").value);
  params["radius"] = Number(document.getElementById("radius").value);
  params["radius_cont"] = Number(document.getElementById("radius_cont").value);
  params["length"] = Number(document.getElementById("length").value);

  var data=[];
  var start = 0;
  var path_num = 0;
  for(var i = 0; i < points.length; i++)  {
    if (i == points.length - 1) {
      console.log(path_num);
      data.push({
        "params": params, 
        "points":points.slice(start),
        "scalars_x":get_data()[path_num]["scalars_x"], 
        "scalars_y":get_data()[path_num]["scalars_y"]});
      }

    if (points[i]["switch"]  == "true") {   
      data.push({
        "params": params, 
        "points":points.slice(start, i + 1),
        "scalars_x":get_data()[path_num]["scalars_x"], 
        "scalars_y":get_data()[path_num]["scalars_y"]});
      start = i;
    
      if (!new_solve) {
        path_num++;
      }  
    }
  }

  $("#loader").show(700);
  
  var data = JSON.stringify(data);
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status) {
    $("#loader").hide(1000);

    new_solve = false;
    new_version(JSON.parse(data));
    update_costs();
  });
}
