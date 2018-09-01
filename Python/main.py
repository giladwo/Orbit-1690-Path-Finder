import math
import plotly
import plotly.graph_objs as go
import time
import path_finder

layout = go.Layout(
    xaxis=go.layout.XAxis(showgrid=True),
    yaxis=go.layout.YAxis(showgrid=True, scaleanchor="x", scaleratio=1))

point1 = path_finder.point(0, 0, math.pi/2)
point2 = path_finder.point(2.5, 0, 280*math.pi/180)#3*math.pi/4 + math.pi)
point3 = path_finder.point(5, 0, math.pi/2)
point4 = path_finder.point(2.5, 0, 260*math.pi/180)#math.pi/4+math.pi)
        
def main():
    path = path_finder.path_finder(point1, point2, point3, point4, point1)

    print (" -started calculating")
    start_time = time.perf_counter()

    fig = plotly.tools.make_subplots(rows=1, cols=1)

    #run with 3rd power
    path.update_poly(3)
    path.find_scalars()

    runtime = (time.perf_counter()- start_time)*60/100
    print (" -found 3! runtime:", "0"+str(int(runtime/60))+":"+str(int(runtime)))
    
    third_power = go.Scatter(
    x=path.draw_graph(0.01)[0], 
    y=path.draw_graph(0.01)[1],
    )

    fig.append_trace(third_power,1,1)
    fig['layout'].update(layout)
    plotly.offline.plot(fig, filename='path_plot.html')
    
    #run with 5th power    
    path.update_poly(5)
    path.find_scalars()
    
    runtime = (time.perf_counter()- start_time)*60/100
    print (" -found 5! runtime:", "0"+str(int(runtime/60))+":"+str(int(runtime)))

    fifth_power = go.Scatter(
    x=path.draw_graph(0.01)[0], 
    y=path.draw_graph(0.01)[1],
    )

    fig.append_trace(fifth_power,1,1)
    fig['layout'].update(layout)
    
    plotly.offline.plot(fig, filename='path_plot.html')
    
    print ("")
    print ("Done!")
    print ("position: ", path.get_position_costs())
    print ("angle: ", path.get_angle_costs())
    print ("radius: ", path.get_radius_cost())
    print ("radius differnce: ", path.get_radius_cont_cost())
    print ("length: ", path.get_length_cost())

if __name__ == '__main__':
    main()