import random

from entities.drawable_entity import DrawableEntity
from entities.message import MESSAGE_WAIT, ComeMessage
from entities.particle import Particle
from entities.rock import Rock
from utils import rect_in_world, rects_are_overlapping, normalize


class Explorer(DrawableEntity):
    SIZE = 7
    MAX_VELOCITY = 1.3
    PICKUP_REACH = 1
    SENSOR_RANGE = 15
    PARTICLE_SENSOR_RANGE = 100
    MAX_NEW_DIRECTION_ATTEMPTS = 5
    SENSE_DELAY = 100
    COLOR = 'blue'
    HAS_ROCK_COLOR = 'yellow'
    SENSOR_COLOR = 'yellow'
    PARTICLE_SENSOR_COLOR = 'red'

    def __init__(self, x, y, world):
        self.x = x
        self.y = y
        self.world = world
        self.dx, self.dy = self._get_new_direction()
        self.ticks = 0
        self.has_rock = False
        self.inbox = []
        self.initial_drop_tick = 0
        self.tick_range_drop_particles = 10

    def draw(self, canvas):
        helper = Explorer(self.x, self.y, self.world)
        helper.SIZE = 2 * self.SENSOR_RANGE + self.SIZE
        top_left, bottom_right = helper.get_bounds()
        canvas.create_oval(top_left.x,
                           top_left.y,
                           bottom_right.x,
                           bottom_right.y,
                           outline=self.SENSOR_COLOR)
        if self.world.type:
            helper = Explorer(self.x, self.y, self.world)
            helper.SIZE = 2 * self.PARTICLE_SENSOR_RANGE + self.SIZE
            top_left, bottom_right = helper.get_bounds()
            canvas.create_oval(top_left.x,
                            top_left.y,
                            bottom_right.x,
                            bottom_right.y,
                            outline=self.PARTICLE_SENSOR_COLOR)
        
        top_left, bottom_right = self.get_bounds()
        canvas.create_rectangle(top_left.x,
                                top_left.y,
                                bottom_right.x,
                                bottom_right.y,
                                outline="",
                                fill=self.HAS_ROCK_COLOR if self.has_rock else self.COLOR)

    def clear_inbox(self):
        self.inbox = []

    def clear_inbox_from(self, source):
        self.inbox = [msg for msg in self.inbox if msg.source != source]

    def transfer_rock_to_carrier(self):
        self.has_rock = False

    def tick(self):
        self._tick()
        self.ticks += 1

    def _tick(self):

        # 1 | avoid obstacles
        if not self._can_move():
            self._agent_avoid_obstacles()
            self._agent_move()

        # 2 | samples and on the ship
        elif self.has_rock and self._drop_available():
            self._agent_drop_sample()
            self._agent_move()
        
        # 3 | samples and not on the ship
        elif self.has_rock:
            self._agent_go_to_ship()
            self._agent_move()
        
        #4 | sample detection
        elif self._sense_rock():
            self._agent_pick()
            self._agent_move()
        #5 | particle detection
        elif self._sense_particle() and self.world.type:
            self._agent_particle()
            self._agent_move()
        #6 | nothing
        else:
            self._agent_move()



    # avoid obstacles | 1
    def _agent_avoid_obstacles(self):
    	new_direction_attempts = 0
    	while not self._can_move() and new_direction_attempts < self.MAX_NEW_DIRECTION_ATTEMPTS:
    		self.dx, self.dy = self._get_new_direction()
    		new_direction_attempts+=1

    # samples and on the ship | 2
    def _agent_drop_sample(self):
    	self.has_rock = False
    	self.world.rock_collected()
    	return

    # samples and not on the ship | 3
    def _agent_go_to_ship(self):
        self.dx, self.dy = normalize(self.world.mars_base.x - self.x,self.world.mars_base.y - self.y)
        #if rock detected and full 
        rock = self._rock_available()

        if rock and self.world.type:
            #drop a particle
            if self.tick_range_drop_particles < self.ticks - self.initial_drop_tick:
                particle = Particle.generate_particle(self.x, self.y)
                self.world.add_entity(particle)
                self.initial_drop_tick = self.ticks
    
    # sample detection | 4
    def _agent_pick(self):
        rock = self._rock_available()
        if rock:
            self.has_rock = True
            self.world.remove_entity(rock)

            #drop a particle
            if self.world.type:
                particle = Particle.generate_particle(self.x, self.y)
                self.world.add_entity(particle)
            
            return
        # Head towards rock.
        rock = self._sense_rock()
        if rock:
            self.dx, self.dy = normalize(rock.x - self.x, rock.y - self.y)
    # particle detection | 5
    def _agent_particle(self):
        particle = self._particle_available()
        if particle:
            self.world.remove_entity(particle)
            return

        particle = self._sense_particle()
        if particle:
            self.dx, self.dy = normalize(particle.x - self.x, particle.y - self.y)
    # nothing | 6
    def _agent_move(self):
    	self._move()

    def _move(self):
        self.x += self.dx
        self.y += self.dy

    def _get_new_direction(self):
        dx = random.uniform(-self.MAX_VELOCITY, self.MAX_VELOCITY)
        dy = random.uniform(-self.MAX_VELOCITY, self.MAX_VELOCITY)
        return normalize(dx, dy)

    def _can_move(self):
        new_self = Explorer(self.x + self.dx,
                            self.y + self.dy,
                            self.world)
        bounds = new_self.get_bounds()

        if not rect_in_world(bounds, new_self.world):
            return False

        for other in new_self.world.entities:
            # Allow collisions with other explorers.
            if isinstance(other, Explorer):
                continue
            #Allow collisions with particles
            if isinstance(other, Particle):
                continue
            if isinstance(other, Rock):
                continue

            if rects_are_overlapping(bounds, other.get_bounds()):
                return False

        return True

    def _rock_available(self):
        for rock in self.world.rocks:
            if rects_are_overlapping(self.get_bounds(),
                                     rock.get_bounds(),
                                     self.PICKUP_REACH):
                return rock

        return None

    def _particle_available(self):
        for particle in self.world.particles:
            if rects_are_overlapping(self.get_bounds(),
                                     particle.get_bounds(),
                                     self.PICKUP_REACH):
                return particle

        return None

    def _sense_rock(self):
        # Wait a bit so that the explorers spread out.
        if self.ticks < self.SENSE_DELAY:
            return None

        for rock in self.world.rocks:
            if rects_are_overlapping(self.get_bounds(),
                                     rock.get_bounds(),
                                     self.SENSOR_RANGE):
                return rock

        return None

    def _sense_particle(self):

        for particle in self.world.particles:
            if rects_are_overlapping(self.get_bounds(),
                                     particle.get_bounds(),
                                     self.PARTICLE_SENSOR_RANGE):
                return particle

        return None

    def _drop_available(self):
        if rects_are_overlapping(self.get_bounds(),
                                 self.world.mars_base.get_bounds(),
                                 self.PICKUP_REACH):
            return True
        return False

    def _incoming_carrier(self):
        incoming = [msg for msg in self.inbox if msg.type == MESSAGE_WAIT]
        if incoming:
            return incoming[0]
        return None

    def _broadcast_come_message(self):
        for carrier in self.world.carriers:
            carrier.inbox.append(ComeMessage(self, self.x, self.y))
