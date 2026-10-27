import math
import time

from pico2d import load_image
from transitions import Machine

RUN_SPEED = 5
AUTO_RUN_SPEED = 10
AUTO_RUN_SIZE = 120
AUTO_RUN_HALF_WIDTH = AUTO_RUN_SIZE // 2
HALF_SPRITE_WIDTH = 50
CANVAS_WIDTH = 800


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.left_pressed = False
        self.right_pressed = False
        self.image = load_image('animation_sheet.png')
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'Sleep', 'AutoRun'],
            transitions=[
                {
                    'trigger': 'animate',
                    'source': 'IDLE',
                    'dest': 'IDLE',
                    'after': 'advance_frame',
                },
                {
                    'trigger': 'start_running',
                    'source': ['IDLE', 'Sleep', 'AutoRun'],
                    'dest': 'RUN',
                    'after': 'reset_run_frame',
                },
                {
                    'trigger': 'start_auto_run',
                    'source': ['IDLE', 'RUN', 'Sleep'],
                    'dest': 'AutoRun',
                    'after': 'reset_run_frame',
                },
                {
                    'trigger': 'stop_running',
                    'source': 'RUN',
                    'dest': 'IDLE',
                    'after': 'reset_idle',
                },
                {
                    'trigger': 'sleep',
                    'source': 'IDLE',
                    'dest': 'Sleep',
                },
                {
                    'trigger': 'wake_up',
                    'source': 'Sleep',
                    'dest': 'IDLE',
                    'after': 'reset_idle_timer',
                },
            ],
            initial='IDLE',
            auto_transitions=False,
        )
        self.idle_started_at = time.monotonic()

    def update(self):
        if self.state == 'IDLE':
            self.machine.dispatch('animate')
            if time.monotonic() - self.idle_started_at >= 5:
                self.machine.dispatch('sleep')
        elif self.state == 'RUN':
            self.advance_frame()
            self.x = min(
                CANVAS_WIDTH - HALF_SPRITE_WIDTH,
                max(HALF_SPRITE_WIDTH, self.x + self.face_dir * RUN_SPEED),
            )
        elif self.state == 'AutoRun':
            self.advance_frame()
            next_x = self.x + self.face_dir * AUTO_RUN_SPEED
            if next_x >= CANVAS_WIDTH - AUTO_RUN_HALF_WIDTH:
                self.x = CANVAS_WIDTH - AUTO_RUN_HALF_WIDTH
                self.face_dir = -1
            elif next_x <= AUTO_RUN_HALF_WIDTH:
                self.x = AUTO_RUN_HALF_WIDTH
                self.face_dir = 1
            else:
                self.x = next_x

    def wake(self):
        if self.state == 'Sleep':
            self.machine.dispatch('wake_up')

    def activate_auto_run(self):
        if self.state != 'AutoRun':
            self.machine.dispatch('start_auto_run')

    def press_direction(self, direction):
        if direction == -1:
            self.left_pressed = True
        else:
            self.right_pressed = True
        self.face_dir = direction

        if self.state in ('IDLE', 'Sleep', 'AutoRun'):
            self.machine.dispatch('start_running')

    def release_direction(self, direction):
        if direction == -1:
            self.left_pressed = False
        else:
            self.right_pressed = False

        if self.state != 'RUN':
            return

        if direction == self.face_dir:
            if self.left_pressed:
                self.face_dir = -1
            elif self.right_pressed:
                self.face_dir = 1
            else:
                self.machine.dispatch('stop_running')

    def reset_run_frame(self):
        self.frame = 0

    def reset_idle(self):
        self.frame = 0
        self.reset_idle_timer()

    def reset_idle_timer(self):
        self.idle_started_at = time.monotonic()

    def advance_frame(self):
        self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.state == 'Sleep':
            source_y = 300 if self.face_dir == 1 else 200
            self.image.clip_composite_draw(
                0, source_y, 100, 100, math.pi / 2, '', self.x, self.y - 30, 100, 100
            )
            return

        if self.state in ('RUN', 'AutoRun'):
            source_y = 100 if self.face_dir == 1 else 0
            if self.state == 'AutoRun':
                self.image.clip_draw(
                    self.frame * 100,
                    source_y,
                    100,
                    100,
                    self.x,
                    self.y,
                    AUTO_RUN_SIZE,
                    AUTO_RUN_SIZE,
                )
            else:
                self.image.clip_draw(
                    self.frame * 100, source_y, 100, 100, self.x, self.y
                )
            return

        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)