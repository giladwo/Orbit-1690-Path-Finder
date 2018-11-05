//var data = "";
var f_ctx;
var p_ctx;

var field_img;
var field_canvas;

var points_canvas;
var pixel_meters;

const default_data = {path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}]}

var parsed_data  = [default_data]; //stores all the data got from python 

var appData;

var clicked_graph = true;

var data_version = 0; //stores current data version
var new_solve    = true; //whether there is data or not

var robot_height = 0.8 //Meters

const POINT_SIZE = 5;
const PATH_SIZE  = 1;

const real_field_width  = 16; //Meters
const real_field_height = 8; //Meters

function toPrec (inp ,prec) {
  ans = inp*Math.pow(10, prec);
  ans = Math.round(ans, 0)/Math.pow(10, prec);
  return(String(ans));
}

function angleRange (angle, radians=true) {
  if (radians) {
    angle *= -180/Math.PI;
  }

  while (angle >= 360) {
    angle -= 360;
  }
 
  while (angle < 0) {
    angle += 360;
  }
  return (angle);
}

class Point {
  constructor(elem) {
    this.color = "rgba(255,255,255, 0.5)";
    this.data = {};  
    this.size = POINT_SIZE;
    this.element = elem; 
    this.getDataFromElement();
  }

  draw(px2m) {
    p_ctx.beginPath();
    p_ctx.arc (this.data["x"]*px2m, this.data["y"]*px2m, this.size, 0, 2*Math.PI);
    p_ctx.fillStyle = this.color;
    p_ctx.fill();
    p_ctx.beginPath();
    let angle = this.data["heading"];
    let armLen = 15;
    p_ctx.strokeStyle = this.color;
    p_ctx.moveTo(this.data["x"]*px2m+Math.cos(angle)*this.size, this.data["y"]*px2m+Math.sin(angle)*this.size);
    p_ctx.lineTo(this.data["x"]*px2m+Math.cos(angle)*armLen, this.data["y"]*px2m+Math.sin(angle)*armLen);
    p_ctx.lineCap = 'round';
    p_ctx.lineWidth = 1;
    p_ctx.stroke();
  }

  distance(point_x, point_y) {
    return Math.sqrt((this.data["x"]-point_x)^2+(this.data["y"]-point_y)^2);
  }

  getDataFromElement () {
    this.data["x"] = Number(this.element.querySelectorAll('.x > input')[0].value);
    this.data["y"] = Number(this.element.querySelectorAll('.y > input')[0].value);
    this.data["heading"] = Number(this.element.querySelectorAll('.heading > input')[0].value)*Math.PI/180;
    this.data["switch"] = String(this.element.querySelectorAll('.switch > label > input')[0].checked);
  }
}

class Points {
  constructor () {
    this.points = [];
    this.amount = 0;
    this.update();
    this.solvePoints = this.points;
  }

  update () {
    this.points = [];
    let points_elements = document.getElementsByClassName("point");
    for (var i = 0; i < points_elements.length; i++) {
      this.points.push(new Point(points_elements[i]));
    }
    this.amount = points_elements.length;
    
    this.add_handlers();
  }

  getData () {
    this.update();
    let points = [];
    for (var i = 0; i < this.amount; i++) {
      points.push(this.points[i].data);
    } 
    return (points);
  }

  getPointByElement (elem) {
    for (var i = 0; i < this.amount; i++) {
      if (this.points[i].element == elem) {
        return this.points[i];
      }
    }
    return null;
  }

  add_handlers () {
    for (var i = 0; i < this.amount; i++)  {
      this.points[i].element.addEventListener('mouseenter', function () {point_hover(this, true);} );
      this.points[i].element.addEventListener('click', function () {point_hover(this, true);} );
      this.points[i].element.addEventListener('mouseleave', function () {point_hover(this, false);} );
    }
  }

  draw () {
    p_ctx.shadowColor = '#101010';
    p_ctx.shadowBlur = 4;

    p_ctx.clearRect(0, 0, points_canvas.width, points_canvas.height);

    for (var i = 0; i < this.amount; i++){
      this.points[i].draw(pixel_meters);
    }
  }

  load () {
    $('#points').html("");
    for (var i = 0; i < this.solvePoints.length; i++) {
      add_point(this.solvePoints[i].data["x"],
                this.solvePoints[i].data["y"],
                this.solvePoints[i].data["heading"],
                this.solvePoints[i].data["switch"],
                false);
    }
    this.points = this.solvePoints;
  }

  savePoints () {
    this.solvePoints = this.points;
  }
}

class Params {
  constructor () {
    this.params = {};
    this.update();
  }

  update () {
    let input_elements = document.getElementsByClassName("form-control-param");
    for (var i = 0; i < input_elements.length; i++) {
      this.params[input_elements[i].getAttribute('id')] = Number(input_elements[i].value);
    }
    this.params['method'] = document.getElementById('method').checked;
  }

  load (path_data) {
    let input_elements = document.getElementsByClassName("form-control-param");
    for (var i = 0; i < input_elements.length; i++) {
      //handle cases where there are no costs (e.g. init)
        input_elements[i].value = this.params[input_elements[i].getAttribute('id')]; 
    }      

    if (path_data[0]["costs"] != null) {
        document.getElementById("pos_cost_val").innerHTML = path_data[0]["costs"]["pos_cost"].toPrecision(3);
        document.getElementById("angle_cost_val").innerHTML = path_data[0]["costs"]["angle_cost"].toPrecision(3);
        document.getElementById("radius_cost_val").innerHTML = path_data[0]["costs"]["radius_cost"].toPrecision(3);
        document.getElementById("radius_cont_cost_val").innerHTML = path_data[0]["costs"]["radius_cont_cost"].toPrecision(3);
        document.getElementById("length_cost_val").innerHTML = path_data[0]["costs"]["length_cost"].toPrecision(3);
    }

    document.getElementById('method').checked = this.params['method'];
  }

  getData () {
    return(this.params);
  }
}

class AppData {
  constructor() {   
    this.version = 0;
    this.name = "untitled";
    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData = [defaultData];
  }

  updateForms () {
    this.solverData[this.version]["params"].load(this.solverData[this.version]["path"]);
    this.solverData[this.version]["points"].load(this.solverData[this.version]["points"]);    
    document.getElementById("auto_name").value = this.name;
  }

  newVersion () {
    if (this.version < this.solverData.length) {
      this.solverData.splice(this.version+1, this.solverData.length);
    }

    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData.push(defaultData);
    this.version ++;

    this.solverData[this.version]["points"].update();
    this.solverData[this.version]["points"].savePoints(); 
  }

  saveSolverData (solverData) {
    this.solverData[this.version]["path"] = solverData["path"];
    this.solverData[this.version]["traj"] = solverData["traj"];
    this.solverData[this.version]["params"].load(this.solverData[this.version]["path"]);
  }

  reset () {
    this.version = 0;
    this.updateForms() ;
  }

  undo () {
    if (this.version > 1) {
      this.version --;
      this.updateForms();
    }
  }

  redo () {
    if (this.version < this.solverData.length -1) {
      this.version ++;
      this.updateForms();
    }
  }

  getParams () {
    return(this.solverData[this.version]["params"]);
  }
  getPoints () {
    return(this.solverData[this.version]["points"]);
  }
  getPath () {
    return(this.solverData[this.version]["path"]);
  }
  getTraj () {
    return(this.solverData[this.version]["traj"]); 
  }

  createTrajFile (prec=3) {
    const divider = "\t"
    let output = ""
    for (var i = 0; i < this.getTraj()  ["time"].length; i++) {
      output += toPrec(this.getTraj()["time"][i], prec) + divider;
      output += toPrec(-1*this.getTraj()["y"][i], prec) + divider; //patch to handle inverted axis
      output += toPrec(this.getTraj()["x"][i], prec) + divider;
      output += toPrec(this.getTraj()["right_vel"][i], prec) + divider;
      output += toPrec(this.getTraj()["left_vel"][i], prec) + divider;
      output += toPrec(angleRange(this.getTraj()["heading"][i]), prec) + divider;
      output += "\n";
    }
    return output;
  }

  createDataFile () {
    return JSON.stringify(this.solverData, null, 2);
  }

  loadData (prevData) {
    //this = prevData;
    
    this.updateForms();
  }
}

function point_hover (elem, hover) {
  point = appData.getPoints().getPointByElement(elem);
  if (hover) {
    point.size = POINT_SIZE*1.2;
    point.color = "rgba(255,255,255, 0.9)";
  }
  else {
    point.size = POINT_SIZE;
    point.color = "rgba(255,255,255, 0.5)";
  }

  appData.getPoints().draw();
}

function get_mouse_pos (canvas, evt) {
  var rect = canvas.getBoundingClientRect();
  return {x: evt.clientX - rect.left, y: evt.clientY - rect.top};
}

function draw_path (path_points){
  let robotWidth = appData.getParams().params["width"];
  f_ctx.beginPath();
  
  var inc = 2; 
  for (var i = 0; i < path_points.length - inc; i+=inc){
    var val = parseInt(i*100/path_points.length);
    color = "#bbbbbb";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();
    
    let x = path_points[i]["x"];
    let y = path_points[i]["y"];
    let x1 = path_points[i+inc]["x"];
    let y1 = path_points[i+inc]["y"];

    let alpha = Math.atan2((y1-y),(x1-x));
    
    x = x + Math.cos(alpha)*robot_height/2;
    y = y + Math.sin(alpha)*robot_height/2;

    let xr = Math.cos(alpha+Math.PI/2)*robotWidth/2 + x;
    let yr = Math.sin(alpha+Math.PI/2)*robotWidth/2 + y;
    
    let xl = Math.cos(alpha-Math.PI/2)*robotWidth/2 + x;
    let yl = Math.sin(alpha-Math.PI/2)*robotWidth/2 + y;

    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
    
    color = "#666666";
    f_ctx.fillStyle = color;

    x = path_points[i]["x"];
    y = path_points[i]["y"];
    
    x = x + Math.cos(alpha+Math.PI)*robot_height/2;
    y = y + Math.sin(alpha+Math.PI)*robot_height/2;

    xr = Math.cos(alpha+Math.PI/2)*robotWidth/2 + x;
    yr = Math.sin(alpha+Math.PI/2)*robotWidth/2 + y;
    
    xl = Math.cos(alpha-Math.PI/2)*robotWidth/2 + x;
    yl = Math.sin(alpha-Math.PI/2)*robotWidth/2 + y;

    f_ctx.beginPath();
    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  for (var i = 0; i < path_points.length; i+=inc){

    let traj_i = parseInt(i*appData.getTraj()["left_vel"].length/path_points.length);
    let vel_hue = Math.abs((appData.getTraj()["left_vel"][traj_i]+appData.getTraj()["right_vel"][traj_i])/2);
    vel_hue = 100-parseInt(vel_hue*100/appData.getParams().getData()["max_vel"]);
    color = "hsl("+vel_hue+",100%,60%)";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();
    f_ctx.arc (path_points[i]["x"]*pixel_meters, path_points[i]["y"]*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  f_ctx.closePath();
}

function init_field() {
  $("#loader").hide();
  //$("#params_cont").blur();
  field_canvas = document.getElementById("field_canvas");
  points_canvas = document.getElementById("points_canvas");

  f_ctx = field_canvas.getContext('2d');
  p_ctx = points_canvas.getContext('2d');
  
  field_img = new Image;

  appData = new AppData();

  field_img.onload = function() {
    f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    appData.getPoints().draw();
  };

  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
}

function draw_field() {
  if (!new_solve) {
    f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    f_ctx.shadowBlur = 0;

      for (var i = 0; i < appData.getPath().length; i++) {
        draw_path(appData.getPath()[i]["path_points"]);
      }
    }
    document.getElementById("version-header").innerHTML = appData.version + " / " + (appData.solverData.length-1)
    
    f_ctx.shadowBlur = 10;
    appData.getPoints().draw();

    update_forms();
}

function update_forms () {
  if (Number(document.getElementById("poly").value) != 5) {
      document.getElementById("method").disabled = true;
      document.getElementById("method").checked = false;
    }
    else {
      document.getElementById("method").disabled = false; 
    }
}

//delete future changes and push new version of paths
function new_version () {
  clicked_graph = false;
  show_graph();
  
  setDuration("Duration: ");
  
  draw_field();
}

function reset () {
  appData.getPoints().update();
  new_solve = true;
  clicked_graph = true;
  if (new_solve) {
    $("#download").hide(300);
    $(".traj-area").hide(200);
  }
  draw_field(); 
}

function change () {
  appData.getPoints().update();
  setDuration("Duration: ");
  clicked_graph = true;
  draw_field();
  $("#download").show(100); 
}

function reset_data () {
  appData.reset();
  reset();
}

function redo_change () {
  appData.redo();
  change();
}

function undo_change () {
  appData.undo();
  change();
}

function add_point (x=1, y=1, angle=0, reverse=false, draw=true) {
  reverse = (reverse === true) ? "checked":"";

  $('#points').append("<tr class='point move-cursor'>"+
    "<td class='delete'><a class='btn btn-link btn-small' onclick='align_robot(this)'>" + 
    "<i class='glyphicon glyphicon-object-align-left glyphicon-small'></i>" +
    "</a></td>" +
    "<td class='x'><input class='form-control form-control-small' type='number' step='0.1' placeholder='X' oninput='reset()' value="+
    //Math.min(real_field_width,(points.getData()[points.amount-1]["x"]+1))+
    x +
    "></td>" +
    "<td class='y'><input class='form-control form-control-small' type='number' step='0.1' placeholder='Y' oninput='reset()' value="+
    //Math.min(real_field_height,(points.getData()[points.amount-1]["y"]+1))+
    y + 
    "></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='reset()' step='5' value="+
    angle*180/Math.PI + 
    "></td>"+
    "<td class='switch'><label class='toggle'><input type='checkbox' onclick='reset()' "+
    reverse +
    "><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");

  if (draw) {
    reset();
  }
}

function delete_point (elem) {
  if (appData.getPoints().amount > 2) {
    $(elem).parent().parent().remove();
    reset();
  }
}

function align_robot (elem) {
  let pointElem = elem.parentNode.parentNode;
  appData.getPoints().getPointByElement(pointElem).data["x"] = appData.getParams().getData()["height"]/2;
  pointElem.querySelectorAll('.x > input')[0].value = appData.getParams().getData()["height"]/2;
  appData.getPoints().getPointByElement(pointElem).data["heading"] = 0;
  pointElem.querySelectorAll('.heading > input')[0].value = 0;
}

function save_traj () {
  const {dialog} = require('electron').remote;
  const fs = require('fs');
  const path = require('path');

  options = {title: "Save Trajectory File", defaultPath: (appData.name + ".txt")}
  console.log(dialog.showSaveDialog(options,(fileName) => {
    if (fileName === undefined) {
        return;
    }

    fs.writeFile(fileName, appData.createTrajFile(), (err) => {
      if (err) console.log(err);
    })

    appData.name = path.basename(fileName).split('.txt')[0];
    appData.updateForms();
  }));
}

function solve() {
  appData.getPoints().update();
  appData.getParams().update();
  
  let points_data = appData.getPoints().getData();
  let params = appData.getParams().getData();
  
  var data=[];
  var start = 0;
  var path_num = 0;
  
  for(var i = 0; i < points_data.length; i++)  {
    if (i == points_data.length - 1) {
      data.push({
        "params": params, 
        "points":points_data.slice(start),
        "scalars_x":appData.getPath()[path_num]["scalars_x"], 
        "scalars_y":appData.getPath()[path_num]["scalars_y"]});
      }
      
      if (points_data[i]["switch"]  == "true") {   
        data.push({
          "params": params, 
          "points":points_data.slice(start, i + 1),
          "scalars_x":appData.getPath()[path_num]["scalars_x"], 
          "scalars_y":appData.getPath()[path_num]["scalars_y"]});
          start = i;
          
          if (!new_solve) {
            path_num++;
          }  
        }
      }
      appData.newVersion();
      
      //$("#params_cont").blur();
      $("#download").hide(300);
      $("#loader").show(300);
      
      var data = JSON.stringify(data);
  
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status) {
    $("#loader").hide(300);
    $("#download").show(300);
    new_solve = false;

    appData.saveSolverData(JSON.parse(data))

    new_version();
  });
}
