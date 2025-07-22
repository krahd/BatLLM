from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
import math


class Bullet:
    def __init__(self, parent_id, x, y, rot):
        self.parent_id = parent_id  # ID of the parent bot
        self.x = x
        self.y = y
        self.rot = rot
        self.step = 0.01  # Step size for movement
        self.radius = 0.02  # Radius of the bullet
        self.colour = (1, 0, 0, 1)  #

    def render(self):
        PushMatrix()
        Translate(self.x, self.y)
        Color(*self.colour)
        Ellipse(pos=(-self.radius / 2, -self.radius / 2), size=(self.radius, self.radius))
        PopMatrix()


    def update(self, bots):
        """Check for out of bounds and collisions with bots.
        Returns a tuple (alive, damaged_bot) where alive is a boolean indicating if the bullet is still alive, and damaged_bot is the ID of the bot that was hit, or None if no bot was hit.
        If the bullet is out of bounds, alive will be False and damaged_bot will be None.
        """
       

        x = self.x
        y = self.y
        nx = x + self.step * math.cos(self.rot)
        ny = y + self.step * math.sin(self.rot)    

      
        

        # Check if the bullet is out of bounds
        if self.x < 0 or self.x > 1 or self.y < 0 or self.y > 1:
            alive = False
            damaged_bot = None
            return alive, damaged_bot
        
        # Check for collision with bots
        for bot in bots:
            if bot.id != self.parent_id:                
                if self.segment_hits_bot(bot, (x, y), (nx, ny)):
                    alive = False
                    damaged_bot = bot.id
                    return alive, damaged_bot
        
        # didn't hit, didn't leave -> update position        
        self.x = nx
        self.y = ny

        alive = True
        damaged_bot = None
        return alive, damaged_bot
                        


    def angle_between(self, p1, p2):
        """Calculate the angle between two points in radians."""        
        angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        return angle % (2 * math.pi)


    def angle_between_vectors(self, v1, v2):
        """Return the counterclockwise angle in radians from v1 to v2, in [0, 2π]."""
        x1, y1 = v1
        x2, y2 = v2

        angle1 = math.atan2(y1, x1)
        angle2 = math.atan2(y2, x2)
        angle = (angle2 - angle1) % (2 * math.pi)

        return angle

    
    def normalize_angle_2pi(self, angle):
        """Normalize angle to [0, 2π]."""
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        while angle < 0:
            angle += 2 * math.pi
        return angle
    


    def segment_hits_bot(self, bot, p1, p2):        
        """
        Check if a line segment p1 → p2 hits the bot and is not blocked by the shield.
        Returns True if bot should take damage.
        """
        cx, cy = bot.x, bot.y
        radius = bot.diameter / 2

        # Line segment vector
        dx = p2[0] - p1[0]   # p2.x - p1.x
        dy = p2[1] - p1[1]   # p2.y - p1.y

        # Vector from center of circle to first point
        fx = p1[0] - cx   # p1.x - cx
        fy = p1[1] - cy   # p1.y - cy

        a = dx**2 + dy**2
        b = 2 * (fx * dx + fy * dy)
        c = fx**2 + fy**2 - radius**2

        discriminant = b**2 - 4 * a * c

        if discriminant < 0:            
            return False  # No intersection

        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)

        for t in (t1, t2):
            if 0 <= t <= 1:                
                # Get point of intersection
                ix = p1[0] + t * dx
                iy = p1[1] + t * dy

                if not bot.shield: #shield is down                     
                    return True
                
                else:
                                    
                     
                    impact_angle = self.angle_between_vectors((0, 0), (ix - cx, iy - cy))


                    sr = math.radians(bot.shield_range)                  

                    shield_angle_min = self.normalize_angle_2pi(bot.rot - sr)
                    shield_angle_max = self.normalize_angle_2pi(bot.rot + sr)


                    print()
                    print("-----")
                    print()
                    print(f"impact_angle: {math.degrees(impact_angle)} \n",
                          f"shield range: {math.degrees(sr)} \n",
                          f"bot.rot: {math.degrees(bot.rot)} \n",
                          f"shield_angle_min: {math.degrees(shield_angle_min)} \n",
                          f"shield_angle_max: {math.degrees(shield_angle_max)} \n\n ")
                    

                    if (impact_angle >= shield_angle_min and impact_angle <= shield_angle_max):
                        print("shb: hit blocked by shield")
                        return False  # Hit blocked by shield

                   

                return True  # Hit

        return False  # No intersection on segment