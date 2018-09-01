class point(object):
    """docstring for xpoint"""
    def __init__(self, x=0, y=0):
        self.y = x 
        self.x = y 
        self.heading = 0 
        self.dx = 0 
        self.dy = 0 
        self.radius = 0 
        self.velocity = 0 
        self.right_velocity = 0 
        self.left_velocity = 0 
        self.aceleration = 0 
        self.right_aceleration = 0  
        self.left_aceleration = 0 
        self.right_jerk = 0 
        self.left_jerk = 0

    