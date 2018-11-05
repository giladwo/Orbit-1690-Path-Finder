from __future__ import division
from matplotlib import pyplot as plt
from scipy import optimize as opt
from utils import trajectory_point

import numpy as np
import math
import json
import sys
import utils

class path_finder(object):
    """docstring for path_finder"""
    POS_COST    = 60000 #60000
    ANGLE_COST  = 6000  #6000
    RADIUS_COST = 50 #50 
    RADIUS_CONT_COST = 10
    LENGTH_COST = 0

    HIGHEST_POLYNOM = 5
    MIN = 0.
    MAX = 1.
    RES = 0.1
    OPTIMIZE_FUNCTION = 'BFGS' #Need to make solver test..
    QUINTIC_OPTIMIZE_FUNCTION = 'Nelder-Mead'
    #'Nelder-Mead' 'Powell' 'CG' 'BFGS' 'Newton-CG' 'L-BFGS-B' 'TNC' 'COBYLA' 'SLSQP' 'trust-constr' 'dogleg' 'trust-ncg' 'trust-exact' 'trust-krylov'
    POWERS = []
    length_cost_val = 0
    
    RADIUS_SEG = 1
    RADIUS_COST_POWER = 1
    
    #                        meters^2                 radians^2                       
    COST_TOLS = {"pos_cost": (10**(-2)) **2 , "angle_cost": (1*math.pi/180) **2, "radius_cost": 1, "radius_cont_cost": 100} 

    #trajectory
    TIME_QUANT  = 1.0 #ms
    DEFAULT_DS = 0.000001
    END_S_THRES = 0.97    

    def __init__(self, params, scalars_x, scalars_y, *args):
        """
        each parameter shold be a tuple of (x, y, angle)
        """
        self.costs = {}
        self.points = args
        self.path_amount = len(self.points)-1
        self.quintic = params.get("method")
        
        self.update_scalars(scalars_x, scalars_y, len(args), params.get("poly", 3))
        self.update_poly(params.get("poly", 3))
        self.update_costs_weights(params)
        self.trajectory = []
    
    def create_linear_scalar(self, param):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            param1 = self.points[index].__getattribute__(param)
            param2 = self.points[index + 1].__getattribute__(param)
            m = (param2 - param1) / (self.MAX - self.MIN)
            b = param1 - self.MIN * m 
            scalars[index][1] = m
            scalars[index][0] = b
        return scalars

    def create_quintic_scalar_x(self):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            self.points[index].update_v(self.points[index+1])
            self.points[index+1].update_v(self.points[index])
            p0 = self.points[index] 
            p1 = self.points[index+1]

            scalars[index][0] = p0.x
            scalars[index][1] = p0.dx
            scalars[index][2] = 0.5*p0.ddx
            scalars[index][3] = -10*p0.x-6*p0.dx-1.5*p0.ddx+0.5*p1.ddx-4*p1.dx+10*p1.x
            scalars[index][4] = 15*p0.x+8*p0.dx+1.5*p0.ddx-p1.ddx+7*p1.dx-15*p1.x
            scalars[index][5] = -6*p0.x-3*p0.dx-0.5*p0.ddx+0.5*p1.ddx-3*p1.dx+6*p1.x

        return scalars

    def create_quintic_scalar_y(self):
        scalars = np.zeros(len(self.points[:-1]) * (self.HIGHEST_POLYNOM + 1)).\
                     reshape(len(self.points[:-1]), (self.HIGHEST_POLYNOM + 1))

        for index in range(len(self.points[:-1])):
            self.points[index].update_v(self.points[index+1])
            self.points[index+1].update_v(self.points[index])
            p0 = self.points[index] 
            p1 = self.points[index+1]

            scalars[index][0] = p0.y
            scalars[index][1] = p0.dy 
            scalars[index][2] = 0.5*p0.ddy
            scalars[index][3] = -10*p0.y-6*p0.dy-1.5*p0.ddy+0.5*p1.ddy-4*p1.dy+10*p1.y
            scalars[index][4] = 15*p0.y+8*p0.dy+1.5*p0.ddy-p1.ddy+7*p1.dy-15*p1.y
            scalars[index][5] = -6*p0.y-3*p0.dy-0.5*p0.ddy+0.5*p1.ddy-3*p1.dy+6*p1.y

        return scalars

    def update_scalars(self, scalars_x, scalars_y, points_amount, wanted_poly):
        if (not scalars_x[0] == None):
            self.HIGHEST_POLYNOM = int(len(scalars_x)/(points_amount-1))-1
            self.scalars_x = np.array(scalars_x).reshape(points_amount-1, self.HIGHEST_POLYNOM+1)
            self.scalars_y = np.array(scalars_y).reshape(points_amount-1, self.HIGHEST_POLYNOM+1)
        
        elif (wanted_poly == 5) and (self.quintic):
            self.scalars_x = self.create_quintic_scalar_x()
            self.scalars_y = self.create_quintic_scalar_y()

        else:
            self.scalars_x = self.create_linear_scalar("x")
            self.scalars_y = self.create_linear_scalar("y")    
    
    def update_poly(self, val):
        poly_diff = val - self.HIGHEST_POLYNOM

        if (poly_diff > 0):
            zeros = np.zeros(len(self.points[:-1]) * (poly_diff)).reshape(len(self.points[:-1]) , poly_diff) 
            self.scalars_x = np.append(self.scalars_x, zeros , 1)
            self.scalars_y = np.append(self.scalars_y, zeros , 1)
        elif (poly_diff < 0):
            self.scalars_x = np.delete(self.scalars_x, np.s_[(abs(poly_diff-2)):], 1)
            self.scalars_y = np.delete(self.scalars_y, np.s_[(abs(poly_diff-2)):], 1)

        self.HIGHEST_POLYNOM = val
        self.POWERS = np.arange(self.HIGHEST_POLYNOM+1)

    def update_costs_weights (self, params):
        self.POS_COST         = params.get("position", 1)*6000000000
        self.ANGLE_COST       = params.get("angle", 1)*6000000000
        self.RADIUS_COST      = params.get("radius", 1)*100
        self.RADIUS_CONT_COST = params.get("radius_cont", 1)*.001
        self.LENGTH_COST      = params.get("length", 0)*0.00001

    def x(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = np.matmul(np.power(s, self.POWERS),(self.scalars_x[index]))
        return answer

    def y(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = np.matmul(np.power(s, self.POWERS),(self.scalars_y[index]))
        return answer

    def dxds(self, index, s):
        answer = np.matmul(np.power(s, self.POWERS[:-1]), (self.scalars_x[index][1:]*self.POWERS[1:]))
        return answer

    def dyds(self, index, s):
        answer = np.matmul(np.power(s, self.POWERS[:-1]), (self.scalars_y[index][1:]*self.POWERS[1:]))
        return answer

    def d2xds2(self, index, s):
        """
        second derivative x
        """
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, 1, -1):
            answer = answer * s + (self.scalars_x[index][i] * i * (i - 1))  
        return answer

    def d2yds2(self, index, s):
        """ 
        second derivative y
        """
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, 1, -1):
            answer = answer * s + (self.scalars_y[index][i] * i * (i - 1))
        return answer
    
    def radius (self, index, s):
        dx = self.dxds(index, s)
        d2x = self.d2xds2(index, s)
        dy = self.dyds(index, s)
        d2y = self.d2yds2(index, s)
        if (((d2x * dy) - (d2y * dx)) == 0):
            return (float(10**5))
        return ((dx ** 2) + (dy ** 2))**1.5 / ((d2x * dy) - (d2y * dx))
    
    def get_position_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            cost += (self.x(index, self.MIN) - self.points[index].x) ** 2
            cost += (self.x(index, self.MAX) - self.points[index + 1].x) ** 2
            cost += (self.y(index, self.MIN) - self.points[index].y) ** 2
            cost += (self.y(index, self.MAX) - self.points[index + 1].y) ** 2
        return cost/((amount_of_points+1) * 4)

    def get_angle_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            start_angle = math.atan2(self.dyds(index, self.MIN), self.dxds(index, self.MIN))
            end_angle = math.atan2(self.dyds(index, self.MAX), self.dxds(index, self.MAX))
            cost += (utils.delta_angle(start_angle, self.points[index].angle)) ** 2
            cost += (utils.delta_angle(end_angle, self.points[index + 1].angle)) ** 2
        return cost / ((amount_of_points+1) * 2)
    
    def get_radius_cost(self):
        cost = 0
        counter = 0
        for index in range(self.path_amount):
            #for s in ( np.cbrt(((np.arange(self.MIN, self.MAX + self.RES,  self.RES))-0.5)*2)*0.5 + 0.5):
            for s in np.arange(self.MIN, self.MAX + self.RES,  self.RES):
                dx = self.dxds(index, s)
                d2x = self.d2xds2(index, s)
                dy = self.dyds(index, s)
                d2y = self.d2yds2(index, s)

                cost +=  (((d2x * dy) - (d2y * dx)) / ((dx ** 2) + (dy ** 2))**1.5)**4

                self.length_cost_val += math.sqrt((self.dxds(index, s)/self.RES)**2 + (self.dyds(index, s)/self.RES)**2)
                
                counter += 1
        cost /= counter
        return cost
    
    def get_length_cost (self):
        return self.length_cost_val

    def get_radius_cont_cost(self):
        cost = 0
        counter = 1

        if (self.path_amount-1 > 0):
            counter = 0

        for index in range(self.path_amount - 1):
            curv = self.radius(index, self.MAX-0.000000001)
            last_curv = self.radius(index+1, self.MIN+0.000000001)
            #curv = math.sqrt(self.d2xds2(index, self.MAX)**2+self.d2yds2(index, self.MAX)**2)
            #last_curv = math.sqrt(self.d2xds2(index+1, self.MIN)**2+self.d2yds2(index+1, self.MIN)**2)
            
            cost += (last_curv-curv) ** 2
            counter += 1
        return cost/counter

    def get_highest_power_cost(self):
        return (sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_x])\
               + sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_y]))

    def get_mag_size_cost (self):
        cost = 0
        for point in self.points:
            mag = point.magnitude_factor
            #cost += ((point.magnitude_factor-1.2))**6 #(0.1**2)*((point.magnitude_factor-1.2))**2
            cost += 415+(-843)*mag+602*(mag**2)+(-177)*(mag**3)+18.5*(mag**4)
        return cost
    
    def cost_function(self, args):
        args = np.array(args)
        
        self.scalars_x = args[:int(len(args) / 2) ]
        self.scalars_y = args[int(len(args) / 2 ):]
        self.scalars_x = np.array(self.scalars_x).reshape(len(self.points) - 1, self.HIGHEST_POLYNOM + 1)
        self.scalars_y = np.array(self.scalars_y).reshape(len(self.points) - 1, self.HIGHEST_POLYNOM + 1)
        
        self.costs["pos_cost"]         = self.get_position_costs()
        self.costs["angle_cost"]       = self.get_angle_costs()
        self.costs["radius_cost"]      = self.get_radius_cost()
        self.costs["radius_cont_cost"] = self.get_radius_cont_cost()
        self.costs["length_cost"]      = self.get_length_cost()

        costs_weighted = {}
        costs_weighted["pos_cost"]         = self.POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = self.ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = self.RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = self.RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = self.LENGTH_COST * self.costs["length_cost"]
        
        return sum(costs_weighted.values())

    def quintic_cost_function(self, args):
        
        for index, point in enumerate(self.points):
            point.ddx = args[index*3]
            point.ddy = args[index*3+1]
            point.magnitude_factor = args[index*3+2]
        
        self.scalars_x = self.create_quintic_scalar_x()
        self.scalars_y = self.create_quintic_scalar_y()
        
        self.costs["pos_cost"]         = self.get_position_costs()
        self.costs["angle_cost"]       = self.get_angle_costs()
        self.costs["radius_cost"]      = self.get_radius_cost()
        self.costs["radius_cont_cost"] = self.get_radius_cont_cost()
        self.costs["length_cost"]      = self.get_length_cost()
        self.costs["mag_size_cost"]    = self.get_mag_size_cost()
        
        costs_weighted = {}
#        costs_weighted["pos_cost"]         = self.POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = self.ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = self.RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = self.RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = self.LENGTH_COST * self.costs["length_cost"]
        costs_weighted["mag_size_cost"]    = 0 * self.costs["mag_size_cost"]
        return sum(costs_weighted.values())

    def get_costs(self):
        return self.costs

    def find_scalars(self):
        if (self.quintic):
            args = []
            for point in self.points:
                args.append(point.ddx)
                args.append(point.ddy)
                args.append(point.magnitude_factor)

            opt.minimize(self.quintic_cost_function, args, method = self.QUINTIC_OPTIMIZE_FUNCTION)
        else:
            opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION)

    def find_trajectory(self, robot, move_dir, time_offset):
        tpoints = [trajectory_point(self.x(0, self.MIN), self.y(0, self.MIN))]
        tpoints[0].reset(robot.max_acc)

        i = 0
        s = self.MAX

        #run forward 
        for path in range(self.path_amount):
            s -= self.MAX
            
            ds_index = 0
            end_ds = []

            while s < self.MAX:
                #choose 's' increment
                if (s*(path+1.0) < (self.END_S_THRES+(self.path_amount-1.0)*self.MAX)):
                    min_vel = abs(tpoints[i].left_vel+tpoints[i].right_vel)/2
                    new_ds = (min_vel*(self.TIME_QUANT/1000.0)) / ((self.dxds(path, s) ** 2 + self.dyds(path, s) ** 2)**0.5)

                    ds = max(new_ds, self.DEFAULT_DS)
                     
                    #too high ds protection   
                    if ds > 0.01:
                        ds = 0.001

                    if (s < (self.MAX-self.END_S_THRES)):
                        end_ds.append(ds)
                        ds_index += 1

                elif ds_index < 0:
                    ds = end_ds[ds_index]
                    ds_index -= 1    
                else:
                    ds = self.DEFAULT_DS

                start_angle = math.atan2(self.dyds(path, s), self.dxds(path, s))
                
                if (s+ds < self.MAX):
                    tpoints.append(trajectory_point(self.x(path, s+ds), self.y(path, s+ds)))
                    end_angle = math.atan2(self.dyds(path, s+ds), self.dxds(path, s+ds))
                elif (path + 1 < self.path_amount):
                    tpoints.append(trajectory_point(self.x(path+1, s+ds-self.MAX), self.y(path+1, s+ds-self.MAX)))
                    end_angle = math.atan2(self.dyds(path+1, s+ds-self.MAX), self.dxds(path+1, s+ds-self.MAX))
                else:
                    break

                tpoints[i+1].update_distances(tpoints[i], start_angle, end_angle, robot.width)

                tpoints[i+1].update_point_forward(tpoints[i], robot.max_vel, robot.max_acc, robot.jerk)

                i += 1
                s += ds

        tpoints[-1].reset(robot.max_acc)

        #run backward
        while (i > 1): 
            tpoints[i-1].update_point_backward(tpoints[i], robot.max_vel, robot.max_acc, robot.jerk)
            i -= 1

        #re calc time by velocities
        tpoints[0].time = time_offset
        for i in range(len(tpoints))[1:]:
            tpoints[i].update_point(tpoints[i-1], move_dir)

        #interpolate to cycle time 
        traj = [trajectory_point(tpoints[0].x, tpoints[0].y, tpoints[0].angle)]
        t = 0
        cycle = (robot.cycle/1000.0) #s
        #calc bias to make sure the last point is when V=0
        bias = tpoints[-1].time-math.floor(tpoints[-1].time/cycle)*cycle 
        traj[0].time = time_offset
        
        for i in range(len(tpoints))[1:]:
            p_time = (t+1)*cycle+bias+time_offset 
            while ((p_time <= tpoints[i].time) and (p_time >= tpoints[i-1].time)):
                t += 1
                
                traj.append(trajectory_point(tpoints[i].x, tpoints[i].y, tpoints[i].angle))
                
                dt  = tpoints[i].time-tpoints[i-1].time
                
                dlv = (tpoints[i].left_vel-tpoints[i-1].left_vel)/dt
                drv = (tpoints[i].right_vel-tpoints[i-1].right_vel)/dt
                dx  = (tpoints[i].x - tpoints[i-1].x)/dt
                dy  = (tpoints[i].y - tpoints[i-1].y)/dt
                da  = (utils.delta_angle(tpoints[i].angle, tpoints[i-1].angle))/dt
                
                traj[t].x = dx*p_time - dx*tpoints[i-1].time + tpoints[i-1].x
                traj[t].y = dy*p_time - dy*tpoints[i-1].time + tpoints[i-1].y
                traj[t].angle = (da*p_time - da*tpoints[i-1].time + tpoints[i-1].angle) % (2*math.pi)
                traj[t].right_vel = drv*p_time - drv*tpoints[i-1].time + tpoints[i-1].right_vel
                traj[t].left_vel  = dlv*p_time - dlv*tpoints[i-1].time + tpoints[i-1].left_vel
                traj[t].right_acc = (traj[t].right_vel - traj[t-1].right_vel)/cycle
                traj[t].left_acc  = (traj[t].left_vel - traj[t-1].left_vel)/cycle
                traj[t].time = p_time
                p_time = (t+1)*cycle+bias+time_offset

        self.trajectory = traj
    
    def draw_graph(self, res):
        xs = []
        ys = []
        for index in range(self.path_amount):
            for s in np.arange(self.MIN, self.MAX + res, res):
                xs.append(self.x(index, s))
        for index in range(self.path_amount):
            for s in np.arange(self.MIN, self.MAX + res, res):
                ys.append(self.y(index, s))
        return (xs,ys)
 
    def create_path_data(self):
        xs, ys = self.draw_graph(0.001)
        path_points = []
        for i in range(len(xs)):
            path_points.append({"x":xs[i], "y":ys[i]})
        data = {"path_points": path_points, "costs": self.costs, "scalars_x": list(np.ravel(self.scalars_x)), "scalars_y": list(np.ravel(self.scalars_y))}
        return data

    def create_traj_data(self):
        data = {'time':[], 'x':[], 'y':[], 'left_vel':[], 'right_vel':[], 'left_acc':[], 'right_acc':[], 'heading':[]}
        for tpoint in self.trajectory:
            data["time"].append(tpoint.time)
            data["x"].append(tpoint.x)
            data["y"].append(tpoint.y)
            data["left_vel"].append(tpoint.left_vel)
            data["right_vel"].append(tpoint.right_vel)
            data["left_acc"].append(tpoint.left_acc)
            data["right_acc"].append(tpoint.right_acc)
            data["heading"].append(tpoint.angle)

        return data

def main(in_data):
    paths = []
    #out_data = {path:[], traj:{x:[], y:[], left_vel:[], right_vel:[], heading:[]}}
    out_data  = {'path':[], 'traj':{}}
    out_data['traj'] = {'time':[], 'x':[], 'y':[], 'left_vel':[], 'right_vel':[], 'left_acc':[], 'right_acc':[], 'heading':[]}
    
    in_data = json.loads(in_data)
    
    #set up path_finder objects
    for index, path_data in enumerate(in_data):
        path_points = [utils.point(
            path_point["x"],
            path_point["y"],
            path_point["heading"])
            for path_point in path_data["points"]]
        
        if (index>0):
            path_points[0].angle += math.pi
        paths.append(path_finder(
            path_data["params"], 
            path_data["scalars_x"],
            path_data["scalars_y"],
            *path_points))
    #setup robot object
    robot = utils.Robot(path_data["params"])
    
    time_offset = 0
    move_dir = 1
    for path in paths:
        #the reason we are all here:
        path.find_scalars()
        path.find_trajectory(robot, move_dir, time_offset)

        #set data to be sent to GUI
        out_data["path"].append(path.create_path_data())
        out_data["traj"] = utils.merge_dicts(out_data["traj"], path.create_traj_data())
        
        time_offset = path.trajectory[-1].time
        move_dir *= -1

    print (json.dumps(out_data))

    #set this to True to open matplotlib for graphing
    if True:
        for path in paths:
            tpoints = path.trajectory

        left_vel  = []
        right_vel = []
        left_acc  = []
        right_acc = []
        times = []

        dts = []

        sim_v  = 0
        sim_head = tpoints[0].angle
        sim_x, sim_y = [tpoints[0].x], [tpoints[0].y]
        
        for i in range(len(tpoints)):
            left_vel.append(tpoints[i].left_vel)
            right_vel.append(tpoints[i].right_vel)

            sim_v = 2*((right_vel[i]+left_vel[i])/2)
            #sim_head = tpoints[i].angle

            if (i < len(tpoints) -1):
                dt = (tpoints[i+1].time-tpoints[i].time)
                
                sim_head += ((right_vel[i]-left_vel[i])/robot.width)*dt
                sim_x.append(sim_x[i-1]+sim_v*math.cos(sim_head)*dt)
                sim_y.append(sim_y[i-1]+sim_v*math.sin(sim_head)*dt)

                left_acc.append((tpoints[i+1].left_vel-tpoints[i].left_vel)/dt)
                right_acc.append((tpoints[i+1].right_vel-tpoints[i].right_vel)/dt)
                dts.append(tpoints[i+1].time-tpoints[i].time)
            
            times.append(tpoints[i].time)

        fig = plt.figure(figsize=(9, 5),dpi=80)
        fig.canvas.set_window_title('Trajectory Graphs')

        traj_p = plt.subplot (3, 1, 1)
        acc_p  = plt.subplot (3, 1, 2)
        path_p = plt.subplot (3, 2, 5)
        dsdt_p = plt.subplot (3, 2, 6)

        indicies = range(len(tpoints)) 

        acc_p.plot(times[:-1], right_acc)
        acc_p.plot(times[:-1], left_acc)
        acc_p.set(xlabel='', ylabel='Acceleration [m/s2]')
        acc_p.grid()

        traj_p.plot(times, right_vel, label='left')
        traj_p.plot(times, left_vel, label='right')
        handles, labels = traj_p.get_legend_handles_labels()
        traj_p.legend(handles, labels)
        traj_p.set(xlabel='', ylabel='Velocity [m/s]')
        traj_p.grid()

        #path_p.scatter(paths[0].draw_graph(0.001)[0], paths[0].draw_graph(0.001)[1], s=3)
        path_p.plot(paths[0].draw_graph(0.001)[0], paths[0].draw_graph(0.001)[1])
        path_p.plot(sim_x, sim_y)
        path_p.set(xlabel='X [m]', ylabel='Y [m]')
        path_p.axis('equal')
        path_p.grid()

        dsdt_p.plot(times[:-1], dts)
        dsdt_p.set(xlabel='time', ylabel='ds/dt [S/s]')
        dsdt_p.grid()
        
        plt.show()
        plt.close('all')

if __name__ == "__main__":
    main(sys.argv[1])
