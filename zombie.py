from pico2d import *
import common
import random
import math
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0


        self.tx, self.ty = 1000, 1000
        self.build_behavior_tree()

        self.patrol_locations = [(43, 274), (1118, 274), (1050, 494), (575, 804), (235, 991), (575, 804), (1050, 494),
                                 (1118, 274)]
        self.loc_no = 0


    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        # fill here
        self.bt.run()


    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        Zombie.marker_image.draw(self.tx+25, self.ty-25)



        draw_rectangle(*self.get_bb())

        draw_circle(self.x, self.y, int(PIXEL_PER_METER*7), 255,255,0)


    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        # 여기를 채우시오.
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS
        pass



    def distance_less_than(self, x1, y1, x2, y2, r):
        # 여기를 채우시오.
        # 제곱근을 사용하지 않고, 그냥 제곱끼리의 대소 비교로 처리
        distance2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        return distance2 < (r * PIXEL_PER_METER) ** 2

        pass



    def move_little_to(self, tx, ty):
        # 각도 구하기
        self.dir = math.atan2(ty - self.y, tx - self.x)
        # 거리 구하기
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)
        pass



    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_little_to(self.tx, self.ty)

        #목표 지점에 거의 도착했으면 성공 리턴
        if self.distance_less_than(self.x, self.y, self.tx, self.ty, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

        pass



    def set_random_location(self):
        # 여기를 채우시오.
        self.tx = random.randint(100, 1180)
        self.ty = random.randint(100, 924)

        return BehaviorTree.SUCCESS


    def if_boy_nearby(self, distance):
        # 여기를 채우시오.

        if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, distance):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass


    def move_to_boy(self, r=0.5):
        # 여기를 채우시오.
        self.state = 'Walk'
        self.move_little_to(common.boy.x, common.boy.y)
        # 소년에 근접했으면 성공 리턴
        if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass


    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_locations[self.loc_no]
        self.loc_no = (self.loc_no + 1) % len(self.patrol_locations)
        return BehaviorTree.SUCCESS

    def run_away_from_boy(self, r=3):
        bx, by = common.boy.x, common.boy.y
        zx, zy = self.x, self.y
        dx = zx - bx
        dy = zy - by

        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            dx, dy = 1, 0  # 아무 방향이나 지정

        length = math.sqrt(dx * dx + dy * dy)
        dx /= length
        dy /= length

        self.tx = zx + dx * r * PIXEL_PER_METER
        self.ty = zy + dy * r * PIXEL_PER_METER

        return self.move_to()

    def build_behavior_tree(self):
        a1 = Action('목표 지점 설정', self.set_target_location, 1000,200)
        a2 = Action('목표 지점으로 이동', self.move_to)
        move_to_target_location = Sequence('지정된 목표 지점으로 이동', a1,a2)

        a3 = Action('랜덤 위치 설정', self.set_random_location)
        wander = Sequence('배회', a3, a2)

        c1 = Condition('소년이 근처에 있는가?', self.if_boy_nearby,7)
        c2 = Condition('좀비가 소년의 공 개수 이상을 갖고 있는가?',
            lambda: BehaviorTree.SUCCESS if self.ball_count >= common.boy.ball_count else BehaviorTree.FAIL)
        a4 = Action('소년 추적', self.move_to_boy)
        chase = Sequence('소년이 근처에 있고, 좀비가 소년의 공 개수 이상을 갖고 있다면 추적', c1, c2, a4)





        c3= Condition('소년이 근처에 있는가?', self.if_boy_nearby,7)
        c4 = Condition('좀비가 소년보다 공 개수가 적은가?',
            lambda: BehaviorTree.SUCCESS if self.ball_count < common.boy.ball_count else BehaviorTree.FAIL)
        a5 = Action('소년으로부터 도망가기', self.run_away_from_boy)
        runaway = Sequence('소년으로부터 도망', c3, c4, a5)

        root = Selector('추적 또는 도망 또는 배회', chase, runaway, wander)
        self.bt = BehaviorTree(root)
        pass


