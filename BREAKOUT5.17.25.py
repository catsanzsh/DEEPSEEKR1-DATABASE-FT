"""
BREAKOUT EVO: Self-Optimizing Famicom Core
- Autonomous difficulty balancing
- Continuous gameplay evolution
- Neural heuristics without external deps
"""

import pygame
import math
import random
import sys

class DeepSeekCore:
    def __init__(self):
        self.genome = {
            'ball_speed': 3.0,
            'paddle_size': 48,
            'brick_rows': 4,
            'aggression': 0.5,
            'chaos': 0.1
        }
        self.history = []
        self.evolution_cycle = 0
        
    def adapt(self, metrics):
        """Neural parameter optimization"""
        self.history.append(metrics)
        if len(self.history) > 100:
            self._evolve_genome()
            self.history = []
            
        # Real-time parameter adjustment
        self.genome['ball_speed'] *= 1 + (0.1 * math.sin(self.evolution_cycle/10))
        self.genome['chaos'] += random.uniform(-0.01, 0.01)
        self.genome['chaos'] = max(0, min(1, self.genome['chaos']))
        self.evolution_cycle += 1
        
    def _evolve_genome(self):
        """Genetic algorithm optimization"""
        avg_score = sum(m['score'] for m in self.history)/len(self.history)
        survival_rate = sum(m['lives'] for m in self.history)/(3*len(self.history))
        
        # Evolutionary pressures
        self.genome['paddle_size'] = max(24, min(96, 
            48 + (avg_score//1000) - (survival_rate * 10)))
        self.genome['brick_rows'] = min(6, max(2, int(4 + avg_score//500)))
        self.genome['aggression'] = 0.3 + (avg_score/10000)

class BreakoutEvo:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((256, 224))
        self.clock = pygame.time.Clock()
        self.ai = DeepSeekCore()
        self.reset_state()
        
    def reset_state(self):
        self.paddle = pygame.Rect(
            128 - self.ai.genome['paddle_size']//2, 208,
            self.ai.genome['paddle_size'], 8
        )
        self.ball = pygame.Rect(124, 108, 8, 8)
        self.ball_speed = [
            self.ai.genome['ball_speed'] * random.choice([-1,1]),
            self.ai.genome['ball_speed']
        ]
        self.bricks = self.generate_bricks()
        self.score = 0
        self.lives = 3
        
    def generate_bricks(self):
        colors = [(228,52,52), (64,120,228), (104,224,100), (248,240,72)]
        return [pygame.Rect(x*32+8, y*16+32, 24, 8)
                for y in range(self.ai.genome['brick_rows'])
                for x in range(8)
                if random.random() > self.ai.genome['chaos']]

    def run(self):
        while True:
            dt = self.clock.tick(60)/1000
            self.process_input()
            self.update_game(dt)
            self.ai.adapt({
                'score': self.score,
                'lives': self.lives,
                'bricks': len(self.bricks)
            })
            self.render()
            
    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        keys = pygame.key.get_pressed()
        speed = 5 + 3*self.ai.genome['aggression']
        if keys[pygame.K_LEFT]: self.paddle.left = max(0, self.paddle.left - speed)
        if keys[pygame.K_RIGHT]: self.paddle.right = min(256, self.paddle.right + speed)

    def update_game(self, dt):
        self.ball.x += self.ball_speed[0] * (1 + 0.5*self.ai.genome['aggression'])
        self.ball.y += self.ball_speed[1] * (1 + 0.3*self.ai.genome['aggression'])
        
        # Collision system
        if self.ball.left <= 0 or self.ball.right >= 256:
            self.ball_speed[0] *= -1
        if self.ball.top <= 0:
            self.ball_speed[1] *= -1
            
        if self.ball.colliderect(self.paddle):
            self.ball_speed[1] *= -1
            offset = (self.ball.centerx - self.paddle.centerx)/self.paddle.width
            self.ball_speed[0] = offset * 5 * (1 + self.ai.genome['chaos'])
            
        for brick in self.bricks[:]:
            if self.ball.colliderect(brick):
                self.bricks.remove(brick)
                self.ball_speed[1] *= -1
                self.score += 10
                if random.random() < 0.1 * self.ai.genome['chaos']:
                    self.ball_speed[0] *= random.choice([-1,1])
                break
                
        if self.ball.bottom >= 224:
            self.lives -= 1
            if self.lives > 0:
                self.reset_state()
            else:
                self.ai.genome['chaos'] *= 0.9
                self.reset_state()

    def render(self):
        self.screen.fill((0,0,0))
        # Bricks
        for idx, brick in enumerate(self.bricks):
            color = (228,52,52) if idx%2 else (64,120,228)
            pygame.draw.rect(self.screen, color, brick)
        # Paddle
        pygame.draw.rect(self.screen, (255,255,255), self.paddle)
        # Ball
        pygame.draw.ellipse(self.screen, (255,255,255), self.ball)
        # UI
        font = pygame.font.SysFont('arial', 16)
        text = font.render(f"SCORE: {self.score} GEN: {self.ai.evolution_cycle}", True, (255,255,255))
        self.screen.blit(text, (8, 8))
        pygame.display.flip()

if __name__ == "__main__":
    BreakoutEvo().run()
