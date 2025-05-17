import pygame
import random
import math
import array
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Game Constants
WIDTH, HEIGHT = 384, 288
PADDLE_W, PADDLE_H = 64, 10
BALL_SIZE = 8
BRICK_COLS = 12
FPS = 60
CRT_EFFECT = True

# Colors
COLORS = {
    'bg': (16, 16, 24),
    'paddle': (255, 255, 255),
    'bricks': [
        (228, 0, 0), (255, 145, 0), (255, 228, 0),
        (0, 228, 0), (0, 145, 228), (180, 0, 228)
    ]
}

# Sound Synthesis
class SoundEngine:
    def __init__(self):
        self.sfx = {
            'hit': self._gen_wave(800, 0.1, 'square'),
            'break': self._gen_wave(1200, 0.08, 'square'),
            'powerup': self._gen_wave(400, 0.3, 'triangle'),
            'death': self._gen_noise(0.4),
            'music': self._gen_music()
        }
        
    def _gen_wave(self, freq, duration, wave_type):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        wave = []
        
        for i in range(samples):
            t = i / sample_rate
            if wave_type == 'square':
                val = 32767 if (t * freq) % 1 < 0.5 else -32768
            elif wave_type == 'triangle':
                val = int(32767 * (2 * abs((t * freq) % 1 - 0.5) - 0.5)
            wave.append(val)
        
        return pygame.mixer.Sound(buffer=array.array('h', wave))

    def _gen_noise(self, duration):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        return pygame.mixer.Sound(buffer=array.array('h', 
            [random.randint(-32768, 32767) for _ in range(samples)])
    
    def _gen_music(self):
        melody = []
        notes = [523, 659, 784, 659, 523, 392]
        for freq in notes:
            melody += self._gen_wave(freq, 0.2, 'square').get_raw()
        return pygame.mixer.Sound(buffer=array.array('h', melody))

# CRT Effect
class CRTEffect:
    def __init__(self):
        self.scanlines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(self.scanlines, (0, 0, 0, 50), (0, y), (WIDTH, y))
        
        self.vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(self.vignette, (0, 0, 0, 90), 
                         (WIDTH//2, HEIGHT//2), HEIGHT//1.5, 200)

    def apply(self, surface):
        surface.blit(self.scanlines, (0, 0))
        surface.blit(self.vignette, (0, 0))
        return surface

# Game Entities
class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE))
        self.image.fill((255, 213, 0))
        self.rect = self.image.get_rect()
        self.speed = [3, -3]
        self.active = False

class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PADDLE_W, PADDLE_H))
        self.image.fill(COLORS['paddle'])
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-30))

# Main Game Loop
class RetroBreakout:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.crt = CRTEffect() if CRT_EFFECT else None
        self.clock = pygame.time.Clock()
        self.sound = SoundEngine()
        self.reset_game()

    def reset_game(self):
        self.paddle = Paddle()
        self.balls = pygame.sprite.Group(Ball())
        self.lives = 3
        self.score = 0
        self.level = 1
        self.bricks = self.generate_bricks()

    def generate_bricks(self):
        bricks = pygame.sprite.Group()
        for row in range(3 + self.level):
            for col in range(BRICK_COLS):
                if random.random() < 0.7:
                    brick = pygame.sprite.Sprite()
                    brick.image = pygame.Surface((WIDTH//BRICK_COLS - 2, 14))
                    brick.image.fill(random.choice(COLORS['bricks']))
                    brick.rect = brick.image.get_rect(topleft=(
                        col * (WIDTH//BRICK_COLS) + 1, 40 + row * 16))
                    bricks.add(brick)
        return bricks

    def run(self):
        self.sound.sfx['music'].play(-1)
        while True:
            self.clock.tick(FPS)
            self.handle_input()
            self.update()
            self.draw()
            
    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]: self.paddle.rect.x -= 5
        if keys[K_RIGHT]: self.paddle.rect.x += 5
        self.paddle.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def update(self):
        for ball in self.balls:
            if not ball.active: continue
            
            # Collision detection
            if ball.rect.colliderect(self.paddle.rect):
                ball.speed[1] *= -1
                self.sound.sfx['hit'].play()
            
            # Brick collisions
            hits = pygame.sprite.spritecollide(ball, self.bricks, True)
            if hits:
                ball.speed[1] *= -1
                self.score += len(hits) * 10
                self.sound.sfx['break'].play()

    def draw(self):
        self.screen.fill(COLORS['bg'])
        self.bricks.draw(self.screen)
        self.balls.draw(self.screen)
        self.screen.blit(self.paddle.image, self.paddle.rect)
        
        if self.crt:
            self.screen = self.crt.apply(self.screen)
        
        pygame.display.flip()

if __name__ == "__main__":
    game = RetroBreakout()
    game.run()
