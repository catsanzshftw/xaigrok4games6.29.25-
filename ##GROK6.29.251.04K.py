import pygame
import numpy as np
import asyncio
import platform

# Constants
WIDTH, HEIGHT = 640, 480
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
PADDLE_SPEED = 3  # Slower paddles for Atari feel
BALL_SPEED = 4    # Slower ball to match Atari pacing
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCANLINE_COLOR = (0, 0, 0, 50)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong: Grok Edition")
clock = pygame.time.Clock()

# Font for scoreboard and text
font = pygame.font.Font(None, 36)

# Procedural sound generation
def make_sound(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    stereo = np.column_stack((wave, wave)).astype(np.float32)
    sound = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))
    return sound

boop_sound = make_sound(440, 0.1)  # Wall hit
beep_sound = make_sound(880, 0.05)  # Paddle hit
score_sound = make_sound(220, 0.2)  # Score

# Game state
class Game:
    def __init__(self):
        self.reset()
        self.ai_active = True
        self.last_update = pygame.time.get_ticks()
        self.insert_coin = True
        self.game_over = False

    def reset(self):
        self.paddle1 = pygame.Rect(50, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.paddle2 = pygame.Rect(WIDTH - 50 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.ball = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.ball_speed = [BALL_SPEED, BALL_SPEED]
        self.score1 = 0
        self.score2 = 0
        self.insert_coin = False
        self.game_over = False

    def update(self):
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update < 32:  # Increased lag to ~30ms for Atari choppiness
            return
        self.last_update = current_time

        # Paddle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and self.paddle1.top > 0:
            self.paddle1.y -= PADDLE_SPEED
        if keys[pygame.K_s] and self.paddle1.bottom < HEIGHT:
            self.paddle1.y += PADDLE_SPEED

        if not self.ai_active:
            if keys[pygame.K_UP] and self.paddle2.top > 0:
                self.paddle2.y -= PADDLE_SPEED
            if keys[pygame.K_DOWN] and self.paddle2.bottom < HEIGHT:
                self.paddle2.y += PADDLE_SPEED
        else:
            # Simple AI: Slower tracking for Atari-like AI
            if self.ball.centery > self.paddle2.centery + 30 and self.paddle2.bottom < HEIGHT:
                self.paddle2.y += PADDLE_SPEED
            if self.ball.centery < self.paddle2.centery - 30 and self.paddle2.top > 0:
                self.paddle2.y -= PADDLE_SPEED

        # Ball movement
        self.ball.x += self.ball_speed[0]
        self.ball.y += self.ball_speed[1]

        # Ball collisions
        if self.ball.top <= 0 or self.ball.bottom >= HEIGHT:
            self.ball_speed[1] = -self.ball_speed[1]
            boop_sound.play()

        if self.ball.colliderect(self.paddle1) or self.ball.colliderect(self.paddle2):
            self.ball_speed[0] = -self.ball_speed[0]
            beep_sound.play()

        # Scoring
        if self.ball.left <= 0:
            self.score2 += 1
            score_sound.play()
            self.ball.center = (WIDTH // 2, HEIGHT // 2)
            self.ball_speed = [BALL_SPEED, BALL_SPEED]
        if self.ball.right >= WIDTH:
            self.score1 += 1
            score_sound.play()
            self.ball.center = (WIDTH // 2, HEIGHT // 2)
            self.ball_speed = [-BALL_SPEED, BALL_SPEED]

        # Win condition
        if self.score1 >= 5 or self.score2 >= 5:
            self.game_over = True

    def draw(self):
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, self.paddle1)
        pygame.draw.rect(screen, WHITE, self.paddle2)
        pygame.draw.rect(screen, WHITE, self.ball)

        # Center line
        for y in range(0, HEIGHT, 10):
            pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 2, y, 4, 4))

        # Scoreboard
        score_text = font.render(f"{self.score1} - {self.score2}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))

        # CRT scanlines
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(screen, SCANLINE_COLOR, (0, y), (WIDTH, y))

        # Insert Coin text
        if self.insert_coin:
            coin_text = font.render("INSERT COIN", True, WHITE)
            screen.blit(coin_text, (WIDTH // 2 - coin_text.get_width() // 2, HEIGHT // 2))

        # Game over prompt
        if self.game_over:
            prompt_text = font.render("Play Again? Y/N", True, WHITE)
            screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2))

game = Game()

async def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    game.reset()
                if event.key == pygame.K_2:
                    game.ai_active = False
                if event.key == pygame.K_1:
                    game.ai_active = True
                if game.game_over:
                    if event.key == pygame.K_y:
                        game.reset()
                    if event.key == pygame.K_n:
                        running = False
                game.insert_coin = False

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
