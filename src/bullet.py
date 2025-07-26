from kivy.graphics import Color, Ellipse, Translate,  PushMatrix, PopMatrix
import math


class Bullet:
    """This class models the bullets shot by the bots. It takes care of its own rendering and the detection of collission against the opponent and the arena's limits.
    """    
    def __init__(self, parent_id, x, y, rot):
        self.parent_id = parent_id  # ID of the parent bot
        self.x = x
        self.y = y
        self.rot = rot
        self.step = 0.01  # Step size for movement
        self.diameter = 0.02  # Diameter of the drawn bullet, internally bullets have no diameter, they are just a point
        self.colour = (1, 0, 0, 1)  #

    def render(self):        
        PushMatrix()
        Translate(self.x, self.y)
        Color(*self.colour)
        Ellipse(pos=(0,0 ), size=(self.diameter, self.diameter))
        PopMatrix()


    def update(self, bots):
        """Check for out of bounds and collisions with bots.

        Args:
            bots (_type_): all the game bots 

        Returns:
            _type_: (alive, damaged_bot_id).
        """
        
        x, y = self.x, self.y
        nx = x + self.step * math.cos(self.rot)
        ny = y + self.step * math.sin(self.rot)

        # Out of bounds check
        if x < 0 or x > 1 or y < 0 or y > 1:
            return False, None

        # Collision check with bots
        dx = nx - x
        dy = ny - y
        for bot in bots:
            if bot.id == self.parent_id:
                continue  # skip the bot that fired this bullet
            hit = self.segment_hits_bot(bot, (x, y), (nx, ny))
            if hit:  
                # Bullet hits the bot (unshielded) – bot takes damage
                return False, bot.id
            
            elif bot.shield:
                # Shield is active and segment_hits_bot returned False.
                # This could mean either a miss or a shield-blocked hit. Check actual intersection.
                cx, cy = bot.x, bot.y
                radius = bot.diameter / 2
                fx = x - cx
                fy = y - cy
                a = dx*dx + dy*dy
                b = 2 * (fx*dx + fy*dy)
                c = fx*fx + fy*fy - radius*radius
                discriminant = b*b - 4*a*c
                if discriminant >= 0:
                    # There is an intersection point(s) with the circle
                    sqrt_disc = math.sqrt(discriminant)
                    t1 = (-b - sqrt_disc) / (2*a)
                    t2 = (-b + sqrt_disc) / (2*a)
                    if (0 <= t1 <= 1) or (0 <= t2 <= 1):
                        # The bullet segment actually intersects the bot's circle -> it was blocked by shield
                        return False, None
        # No collision with any bot; update bullet position
        self.x, self.y = nx, ny
        return True, None

    def segment_hits_bot(self, bot, p1, p2):
        """Determines if the line segment from p1 to p2 hits the bot in an unshielded area.

        Args:
            bot (_type_): the bot
            p1 (_type_): segment start
            p2 (_type_): segment end

        Returns:
            _type_: True if the bot is hit (taking damage), or False if no hit or the hit is blocked by the shield
        """        
        
        cx, cy = bot.x, bot.y
        radius = bot.diameter / 2

        # Segment vector
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        # Vector from bot center to p1
        fx = p1[0] - cx
        fy = p1[1] - cy

        # Quadratic coefficients for line-circle intersection
        a = dx**2 + dy**2
        b = 2 * (fx*dx + fy*dy)
        c = fx**2 + fy**2 - radius**2
        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            return False  # no intersection with the circle

        # Find intersection parameter t (0<=t<=1 for intersections along the segment)
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        hit_t = None

        if 0 <= t1 <= 1:
            hit_t = t1
        elif 0 <= t2 <= 1:
            hit_t = t2
        if hit_t is None:
            return False  # intersection point not within this segment step

        # Compute intersection point
        hit_x = p1[0] + hit_t * dx
        hit_y = p1[1] + hit_t * dy

        # If shield is down, any intersection means a hit
        if not bot.shield:
            return True

        # Shield is active: check if impact point is within shielded arc
        impact_angle = math.atan2(hit_y - cy, hit_x - cx)
        shield_half_angle = math.radians(bot.shield_range)  # half of the shield coverage, in radians

        # Calculate smallest angular difference between impact direction and bot's facing direction
        diff = (impact_angle - bot.rot + math.pi) % (2*math.pi) - math.pi

        # If the impact angle falls within the shield arc, the shield blocks the hit
        if abs(diff) <= shield_half_angle:

            print ("The shield blocked the hit.")
            return False  # hit was on the shielded portion
        # Otherwise, the hit lands on an unshielded portion of the bot
        return True