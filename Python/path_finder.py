from scipy import optimize as opt
import numpy as np
import math
import json
import sys

POS_COST    = 60000 #1000000
ANGLE_COST  = 6000  #80000
RADIUS_COST = 50 #1000 
RADIUS_CONT_COST = 10
LENGTH_COST = 0

class point(object):
    """docstring for dot"""
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

class path_finder(object):
    """docstring for path_finder"""

    HIGHEST_POLYNOM = 5
    MIN = -1.
    MAX = 1.
    RES = 0.2
    OPTIMIZE_FUNCTION = 'BFGS'
            #'Nelder-Mead' 'Powell' 'CG' 'BFGS' 'Newton-CG' 'L-BFGS-B' 'TNC' 'COBYLA' 'SLSQP' 'trust-constr' 'dogleg' 'trust-ncg' 'trust-exact' 'trust-krylov'
    RADIUS_SEG = 1
    RADIUS_COST_POWER = 1
    #                        meters^2                 radians^2                       
    COST_TOLS = {"pos_cost": (10**(-2)) **2 , "angle_cost": (1*math.pi/180) **2, "radius_cost": 1, "radius_cont_cost": 100} 

    # miliseconds
    TIME_QUANT = 2

    def __init__(self, *args):
        """
        each parameter shold be a tuple of (x, y, angle)
        """
        self.costs = {}
        self.points = np.array(args)
        self.scalars_x = self.create_linear_scalar("x")
        self.scalars_y = self.create_linear_scalar("y")
        self.path_amount = len(self.scalars_x)
        self.length_cost = 0

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

    def x(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, -1, -1):
            answer = answer * s + self.scalars_x[index][i]
        return answer

    def y(self, index, s):
        """
        :param int index: the index of the path
        :param float s: the index of s betwin MIN to MAX
        """
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, -1, -1):
            answer = answer * s + self.scalars_y[index][i]
        return answer

    def dxds(self, index, s):
        answer = 0.
        for i in range(len(self.scalars_x[index]) - 1, 0, -1):
            answer = answer * s + (self.scalars_x[index][i] * i)
        return answer

    def dyds(self, index, s):
        answer = 0.
        for i in range(len(self.scalars_y[index]) - 1, 0, -1):
            answer = answer * s + (self.scalars_y[index][i] * i)
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
    
    def delta_angle(self, angle1, angle2):
        delta = angle1 - angle2
        if  delta > math.pi:
            delta -= 2 * math.pi
        elif delta < -math.pi:
            delta += 2 * math.pi
        return delta
    
    def get_position_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            cost += (self.x(index, self.MIN) - self.points[index].x) ** 2
            cost += (self.x(index, self.MAX) - self.points[index + 1].x) ** 2
            cost += (self.y(index, self.MIN) - self.points[index].y) ** 2
            cost += (self.y(index, self.MAX) - self.points[index + 1].y) ** 2
        return cost/(amount_of_points * 4)

    def get_angle_costs(self):
        cost = 0.
        amount_of_points = self.path_amount
        for index in range(amount_of_points):
            start_angle = math.atan2(self.dyds(index, self.MIN), self.dxds(index, self.MIN))
            end_angle = math.atan2(self.dyds(index, self.MAX), self.dxds(index, self.MAX))
            cost += (self.delta_angle(start_angle, self.points[index].angle)) ** 2
            cost += (self.delta_angle(end_angle, self.points[index + 1].angle)) ** 2
        return cost / (amount_of_points * 2)
    
    def get_radius_cost(self):
        cost = 0
        counter = 1
        for index in range(self.path_amount):
            for s in np.arange(self.MIN, self.MAX + self.RES,  self.RES * self.RADIUS_SEG):
                dx = self.dxds(index, s)
                d2x = self.d2xds2(index, s)
                dy = self.dyds(index, s)
                d2y = self.d2yds2(index, s)
                cost += (((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5)) ** 4

                self.length_cost += math.sqrt((dx/self.RES)**2 + (dy/self.RES)**2)
                counter += 1
        cost /= counter
        self.length_cost /= counter
        return cost
    
    def get_length_cost (self):
        return self.length_cost

    def get_radius_cont_cost(self):
        cost = 0
        last_rad = 0

        for index in range(self.path_amount - 1):
            dx = self.dxds(index, 1)
            d2x = self.d2xds2(index, 1)
            dy = self.dyds(index, 1)
            d2y = self.d2yds2(index, 1)
            rad = ((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5)
            
            dx = self.dxds(index+1, -1)
            d2x = self.d2xds2(index+1, -1)
            dy = self.dyds(index+1, -1)
            d2y = self.d2yds2(index+1, -1)
            last_rad = ((d2x * dy) - (d2y * dx)) / (((dx ** 2) + (dy ** 2)) ** 1.5) 
            
            cost += (last_rad-rad) ** 2

        return cost

    def get_highest_power_cost(self):
        return (sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_x])\
               + sum([scalar[self.HIGHEST_POLYNOM] ** 2 for scalar in self.scalars_y]))

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
        costs_weighted["pos_cost"]         = POS_COST * self.costs["pos_cost"]
        costs_weighted["angle_cost"]       = ANGLE_COST * self.costs["angle_cost"]
        costs_weighted["radius_cost"]      = RADIUS_COST * self.costs["radius_cost"]
        costs_weighted["radius_cont_cost"] = RADIUS_CONT_COST * self.costs["radius_cont_cost"]
        costs_weighted["length_cost"]      = LENGTH_COST * self.costs["length_cost"]

        return sum(costs_weighted.values())

    def get_costs(self):
        return self.costs

    def find_scalars(self):
        #return opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION, cost_tol = self.COST_TOLS, get_costs = self.get_costs)
        return opt.minimize(self.cost_function, np.ravel([self.scalars_x, self.scalars_y]), method = self.OPTIMIZE_FUNCTION)
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

    def find_velocities(self):
        xpoints = [xpoint(self.x(0, -1), self.y(0, -1))]
        xpoint_index = 0

        for path in range(self.path_amount):
            s = -1
            while s <= 1:
                ds = xpoints[xpoint_index].velocity * TIME_QUANT / Sqr(self.dxds(path, s) ^ 2 + self.dyds(path, s) ^ 2)


                xpoint_index += 1

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

    def print_path(self):
        xs, ys = self.draw_graph(0.01)
        points = []
        for i in range(len(xs)):
            points.append({"x":xs[i], "y":ys[i]})
        print(json.dumps(points))

def main(data):
    data = json.loads(data)
    points = data["points"]
    params = data["params"]

    path_points = [point(path_point["x"], path_point["y"], path_point["heading"]) for path_point in points]
    path = path_finder(*path_points)

    path.update_poly(params.get("poly", 3))
    POS_COST    = params.get("pos", 60000)
    ANGLE_COST  = params.get("angle", 6000)
    RADIUS_COST = params.get("radius", 50) 
    RADIUS_CONT_COST = params.get("radius_cont", 10)
    LENGTH_COST = params.get("length", 0)
    path.find_scalars()
    path.print_path()

if __name__ == '__main__':
    main(sys.argv[1])
