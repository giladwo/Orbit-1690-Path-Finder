var resetVelFnc;
var resetAccFnc;

function show_graph () {
  clicked_graph = !clicked_graph
  if (clicked_graph) {
    $(".traj-area").hide(200)
  }
  else {
    $(".traj-area").show(200) 
    
    setTimeout(function() {
      draw_traj();        
    }, 200);
  }
}

function draw_traj () {
  new Chartist.Line('#vel-chart', {
    labels: [appData.getTraj()["time"]],
    series: [
      setToGraph(appData.getTraj()["time"], appData.getTraj()["right_vel"]),
      setToGraph(appData.getTraj()["time"], appData.getTraj()["left_vel"])
    ],}, {
    axisX: {
      type: Chartist.AutoScaleAxis,
      showGrid: true,
      showLabel: true,
    },
    plugins: [
      Chartist.plugins.zoom({onZoom : onZoomVel})//{ onZoom: onZoom })
    ],
    chartPadding: {
      right: 40
    },
    lineSmooth: false
    });

    new Chartist.Line('#acc-chart', {
    labels: [appData.getTraj()["time"]],
    series: [
      setToGraph(appData.getTraj()["time"], appData.getTraj()["right_acc"]),
      setToGraph(appData.getTraj()["time"], appData.getTraj()["left_acc"])
    ],}, {
    axisX: {
      type: Chartist.AutoScaleAxis,
      showGrid: true,
      showLabel: true,
    },
      labels: [appData.getTraj()["time"],appData.getTraj()["time"]],
    plugins: [
      Chartist.plugins.zoom({onZoom : onZoomAcc})//{ onZoom: onZoom })
    ],
    chartPadding: {
      right: 40
    },
    lineSmooth: false
    });
}

function setDuration (preText) {
  let path_dur = appData.getTraj()["time"][appData.getTraj()["time"].length-1].toPrecision(3);
  document.getElementById('time-header').innerHTML =  preText + path_dur + " s";
}

function onZoomVel(chart, reset) {
  resetVelFnc = reset;
  $('#vel-zoom-icon').show(200);
}

function onZoomAcc(chart, reset) {
  resetAccFnc = reset;
  $('#acc-zoom-icon').show(200);
}

function resetVelGraph () {
  resetVelFnc && resetVelFnc();
  resetVelFnc = null;
  $('#vel-zoom-icon').hide(200);
}

function resetAccGraph () {
  resetAccFnc && resetAccFnc();
  resetAccFnc = null;
  $('#acc-zoom-icon').hide(200);
}

