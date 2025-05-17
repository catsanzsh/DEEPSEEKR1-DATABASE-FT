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

# Game States
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    CREDITS = 3

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

# Game States Implementation
class MainMenu:
    def __init__(self, game):
        self.game = game
        self.options = ["Play", "Credits", "Exit"]
        self.selected = 0
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 48)

    def handle_input(self, event):
        if event.type == KEYDOWN:
            if event.key == K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == K_SPACE:
                if self.options[self.selected] == "Play":
                    self.game.start_new_game()
                elif self.options[self.selected] == "Credits":
                    self.game.current_state = GameState.CREDITS
                elif self.options[self.selected] == "Exit":
                    pygame.quit()
                    exit()

    def draw(self, screen):
        screen.fill(COLORS['bg'])
        title = self.title_font.render("RETRO BREAKOUT", True, COLORS['text'])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        for i, option in enumerate(self.options):
            color = COLORS['text'] if i != self.selected else (255, 0, 0)
            text = self.font.render(option, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 150 + i*40))
        
        footer = self.font.render("Use ARROW KEYS and SPACE", True, COLORS['text'])
        screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 50))

class PlayState:
    def __init__(self, game):
        self.game = game
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

    def handle_input(self, event):
        if event.type == KEYDOWN:
            if event.key == K_SPACE and not self.ball.active:
                self.ball.active = True
                self.ball.speed = [random.choice([-5, 5]), -5]
                self.game.sound.sfx['start'].play()

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

        if self.ball.rect.colliderect(self.paddle.rect):
            self.handle_paddle_collision()
            
        brick_hit = pygame.sprite.spritecollideany(self.ball, self.bricks)
        if brick_hit:
            self.handle_brick_collision(brick_hit)

        if self.ball.rect.bottom > HEIGHT:
            self.handle_ball_loss()

        if len(self.bricks) == 0:
            self.level_up()

    def handle_paddle_collision(self):
        self.ball.speed[1] *= -1
        offset = (self.ball.rect.centerx - self.paddle.rect.centerx) / (PADDLE_W/2)
        self.ball.speed[0] = offset * 7
        self.ball.speed[1] = -abs(self.ball.speed[1])
        self.game.sound.sfx['hit'].play()

    def handle_brick_collision(self, brick):
        brick.kill()
        self.score += 10
        self.ball.speed[1] *= -1
        self.game.sound.sfx['break'].play()

    def handle_ball_loss(self):
        self.lives -= 1
        self.game.sound.sfx['death'].play()
        if self.lives <= 0:
            self.game_over = True
            self.game.show_game_over(self.score, self.level)
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

    def draw(self, screen):
        screen.fill(COLORS['bg'])
        self.bricks.draw(screen)
        screen.blit(self.paddle.image, self.paddle.rect)
        screen.blit(self.ball.image, self.ball.rect)
        
        score_text = self.game.font.render(f"Score: {self.score}", True, COLORS['text'])
        lives_text = self.game.font.render(f"Lives: {self.lives}", True, COLORS['text'])
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (WIDTH - 100, 10))

class GameOverState:
    def __init__(self, game, final_score, final_level):
        self.game = game
        self.final_score = final_score
        self.final_level = final_level
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 48)

    def handle_input(self, event):
        if event.type == KEYDOWN:
            if event.key == K_r:
                self.game.start_new_game()
            elif event.key == K_ESCAPE:
                self.game.current_state = GameState.MENU

    def draw(self, screen):
        screen.fill(COLORS['bg'])
        title = self.title_font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        score_text = self.font.render(f"Final Score: {self.final_score}", True, COLORS['text'])
        level_text = self.font.render(f"Level Reached: {self.final_level}", True, COLORS['text'])
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 150))
        screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 200))
        
        retry = self.font.render("Press R to Retry", True, COLORS['text'])
        menu = self.font.render("Press ESC for Menu", True, COLORS['text'])
        screen.blit(retry, (WIDTH//2 - retry.get_width()//2, 300))
        screen.blit(menu, (WIDTH//2 - menu.get_width()//2, 350))

class CreditsState:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 48)

    def handle_input(self, event):
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            self.game.current_state = GameState.MENU

    def draw(self, screen):
        screen.fill(COLORS['bg'])
        title = self.title_font.render("CREDITS", True, COLORS['text'])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        lines = [
            "Developed using DeepSeek AI",
            "Published by Flames Co.",
            "Special thanks to:",
            "Pygame Community",
            "Open Source Contributors",
            " ",
            "© 20XX Flames Co.",
            "All rights reserved"
        ]
        
        for i, line in enumerate(lines):
            text = self.font.render(line, True, COLORS['text'])
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 150 + i*30))

class RetroBreakout:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.crt = CRTEffect() if CRT_EFFECT else None
        self.clock = pygame.time.Clock()
        self.sound = SoundEngine()
        self.font = pygame.font.Font(None, 24)
        self.current_state = GameState.MENU
        self.state_handlers = {
            GameState.MENU: MainMenu(self),
            GameState.PLAYING: None,
            GameState.GAME_OVER: None,
            GameState.CREDITS: CreditsState(self)
        }
        pygame.display.set_caption("Retro Breakout 5130X")

    def start_new_game(self):
        self.state_handlers[GameState.PLAYING] = PlayState(self)
        self.current_state = GameState.PLAYING

    def show_game_over(self, final_score, final_level):
        self.state_handlers[GameState.GAME_OVER] = GameOverState(self, final_score, final_level)
        self.current_state = GameState.GAME_OVER

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return
                
                handler = self.state_handlers.get(self.current_state)
                if handler:
                    handler.handle_input(event)

            if self.current_state == GameState.PLAYING:
                self.state_handlers[GameState.PLAYING].update()
                
            self.screen.fill(COLORS['bg'])
            handler = self.state_handlers.get(self.current_state)
            if handler:
                handler.draw(self.screen)
            
            if self.crt:
                self.screen = self.crt.apply(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = RetroBreakout()
    game.run()
