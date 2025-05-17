import pygame
import random

# Initialize Pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 256, 224
PADDLE_WIDTH, PADDLE_HEIGHT = 48, 8
BALL_SIZE = 6
BRICK_WIDTH, BRICK_HEIGHT = 32, 16
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
COLORS = [
    (255, 0, 0),
    (255, 165, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 0, 255)
]

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Breakout")
clock = pygame.time.Clock()

class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PADDLE_WIDTH, PADDLE_HEIGHT))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-30))
        self.speed = 4

    def update(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.speed = [3, -3]
        self.active = False

    def update(self):
        if self.active:
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]

            # Wall collisions
            if self.rect.left <= 0 or self.rect.right >= WIDTH:
                self.speed[0] *= -1
            if self.rect.top <= 0:
                self.speed[1] *= -1

class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

def create_bricks():
    bricks = pygame.sprite.Group()
    for row in range(5):
        for col in range(WIDTH // BRICK_WIDTH):
            color = COLORS[row % len(COLORS)]
            bricks.add(Brick(col*BRICK_WIDTH, 40 + row*BRICK_HEIGHT, color))
    return bricks

def main():
    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks()
    lives = 3
    score = 0

    all_sprites = pygame.sprite.Group()
    all_sprites.add(paddle, ball, bricks)

    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not ball.active:
                    ball.active = True

        # Update
        paddle.update(keys)
        ball.update()

        # Ball-paddle collision
        if ball.rect.colliderect(paddle.rect) and ball.speed[1] > 0:
            ball.speed[1] *= -1
            # Add slight angle variation based on hit position
            offset = (ball.rect.centerx - paddle.rect.centerx) / (PADDLE_WIDTH/2)
            ball.speed[0] = offset * 4

        # Ball-brick collisions
        hit_bricks = pygame.sprite.spritecollide(ball, bricks, True)
        if hit_bricks:
            ball.speed[1] *= -1
            score += len(hit_bricks) * 10

        # Ball reset
        if ball.rect.bottom >= HEIGHT:
            lives -= 1
            if lives <= 0:
                running = False
            else:
                ball.active = False
                ball.rect.center = (WIDTH//2, HEIGHT//2)
                paddle.rect.center = (WIDTH//2, HEIGHT-30)

        # Drawing
        screen.fill(BLACK)
        all_sprites.draw(screen)
        
        # UI elements
        font = pygame.font.Font(None, 16)
        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(score_text, (8, 8))
        screen.blit(lives_text, (WIDTH - 64, 8))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
