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
    'ball': (255, 213, 0),
    'bricks': [
        (228, 0, 0), (255, 145, 0), (255, 228, 0),
        (0, 228, 0), (0, 145, 228), (180, 0, 228)
    ],
    'text': (200, 200, 200)
}

# Sound Synthesis
class SoundEngine:
    def __init__(self):
        self.sfx = {
            'hit': self._gen_wave(800, 0.1, 'square'),
            'break': self._gen_wave(1200, 0.08, 'square'),
            'death': self._gen_noise(0.4),
            'start': self._gen_wave(1000, 0.2, 'saw')
        }
        
    def _gen_wave(self, freq, duration, wave_type):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        wave = array.array('h')
        
        for i in range(samples):
            t = i / sample_rate
            if wave_type == 'square':
                val = 32767 if (t * freq) % 1 < 0.5 else -32768
            elif wave_type == 'saw':
                val = int(32767 * (2 * (t * freq % 1) - 1))
            wave.append(val)
        
        return pygame.mixer.Sound(buffer=wave)

    def _gen_noise(self, duration):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        return pygame.mixer.Sound(buffer=array.array('h', 
            [random.randint(-32768, 32767) for _ in range(samples)]))

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
        self.image.fill(COLORS['ball'])
        self.rect = self.image.get_rect()
        self.speed = [0, 0]
        self.active = False
        self.max_speed = 8

    def update(self):
        if self.active:
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]
            
            # Wall collisions
            if self.rect.left < 0 or self.rect.right > WIDTH:
                self.speed[0] *= -1
            if self.rect.top < 0:
                self.speed[1] *= -1

class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PADDLE_W, PADDLE_H))
        self.image.fill(COLORS['paddle'])
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-30))
        self.speed = 8

# Main Game Loop
class RetroBreakout:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.crt = CRTEffect() if CRT_EFFECT else None
        self.clock = pygame.time.Clock()
        self.sound = SoundEngine()
        self.font = pygame.font.Font(None, 24)
        self.reset_game()

    def reset_game(self):
        self.paddle = Paddle()
        self.ball = Ball()
        self.ball.rect.center = (WIDTH//2, HEIGHT//2)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.bricks = self.generate_bricks()
        self.game_over = False
        self.ball.active = False

    def generate_bricks(self):
        bricks = pygame.sprite.Group()
        rows = min(3 + self.level, 8)
        for row in range(rows):
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
        while True:
            self.clock.tick(FPS)
            self.handle_input()
            self.update()
            self.draw()
            
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == KEYDOWN:
                if event.key == K_SPACE and not self.ball.active:
                    self.ball.active = True
                    self.ball.speed = [random.choice([-5, 5]), -5]
                    self.sound.sfx['start'].play()
                if event.key == K_r and self.game_over:
                    self.reset_game()

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]: 
            self.paddle.rect.x -= self.paddle.speed
        if keys[K_RIGHT]: 
            self.paddle.rect.x += self.paddle.speed
        self.paddle.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def update(self):
        if self.game_over:
            return

        self.ball.update()

        # Ball-paddle collision
        if self.ball.rect.colliderect(self.paddle.rect):
            self.handle_paddle_collision()
            
        # Brick collisions
        brick_hit = pygame.sprite.spritecollideany(self.ball, self.bricks)
        if brick_hit:
            self.handle_brick_collision(brick_hit)

        # Bottom boundary check
        if self.ball.rect.bottom > HEIGHT:
            self.handle_ball_loss()

        # Level completion
        if len(self.bricks) == 0:
            self.level_up()

    def handle_paddle_collision(self):
        self.ball.speed[1] *= -1
        offset = (self.ball.rect.centerx - self.paddle.rect.centerx) / (PADDLE_W/2)
        self.ball.speed[0] = offset * 7
        self.ball.speed[1] = -abs(self.ball.speed[1])
        self.sound.sfx['hit'].play()

    def handle_brick_collision(self, brick):
        brick.kill()
        self.score += 10
        self.ball.speed[1] *= -1
        self.sound.sfx['break'].play()

    def handle_ball_loss(self):
        self.lives -= 1
        self.sound.sfx['death'].play()
        if self.lives <= 0:
            self.game_over = True
        else:
            self.ball.active = False
            self.ball.rect.center = (WIDTH//2, HEIGHT//2)
            self.paddle.rect.center = (WIDTH//2, HEIGHT-30)

    def level_up(self):
        self.level += 1
        self.ball.speed = [s * 1.1 for s in self.ball.speed]
        self.bricks = self.generate_bricks()
        self.ball.active = False
        self.ball.rect.center = (WIDTH//2, HEIGHT//2)
        self.paddle.rect.center = (WIDTH//2, HEIGHT-30)

    def draw(self):
        self.screen.fill(COLORS['bg'])
        
        # Draw game elements
        self.bricks.draw(self.screen)
        self.screen.blit(self.paddle.image, self.paddle.rect)
        self.screen.blit(self.ball.image, self.ball.rect)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, COLORS['text'])
        lives_text = self.font.render(f"Lives: {self.lives}", True, COLORS['text'])
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (WIDTH - 100, 10))
        
        if self.game_over:
            go_text = self.font.render("GAME OVER - PRESS R", True, COLORS['text'])
            self.screen.blit(go_text, (WIDTH//2 - 100, HEIGHT//2))
        
        if self.crt:
            self.screen = self.crt.apply(self.screen)
        
        pygame.display.flip()

if __name__ == "__main__":
    game = RetroBreakout()
    game.run()
