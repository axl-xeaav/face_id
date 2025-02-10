import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship Game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Player spaceship
player_width = 50
player_height = 50
player_x = SCREEN_WIDTH // 2 - player_width // 2
player_y = SCREEN_HEIGHT - player_height - 10
player_speed = 5

# Enemy spaceship
enemy_width = 50
enemy_height = 50
enemy_speed = 3
enemies = []

# Bullet
bullet_width = 5
bullet_height = 15
bullet_speed = 9
bullets = []

# Explosion
explosion_radius = 50
explosions = []

# Clock
clock = pygame.time.Clock()

# Function to reset the game
def reset_game():
    global player_x, player_y, enemies, bullets, explosions, game_over
    player_x = SCREEN_WIDTH // 2 - player_width // 2
    player_y = SCREEN_HEIGHT - player_height - 10
    enemies.clear()
    bullets.clear()
    explosions.clear()
    game_over = False

# Function to draw the player
def draw_player(x, y):
    pygame.draw.rect(screen, GREEN, (x, y, player_width, player_height))

# Function to draw an enemy
def draw_enemy(x, y):
    pygame.draw.rect(screen, RED, (x, y, enemy_width, enemy_height))

# Function to draw a bullet
def draw_bullet(x, y):
    pygame.draw.rect(screen, WHITE, (x, y, bullet_width, bullet_height))

# Function to draw an explosion
def draw_explosion(x, y):
    pygame.draw.circle(screen, YELLOW, (x, y), explosion_radius)

# Function to spawn enemies
def spawn_enemy():
    enemy_x = random.randint(0, SCREEN_WIDTH - enemy_width)
    enemy_y = -enemy_height
    enemies.append([enemy_x, enemy_y, random.choice([-1, 1])])  # Add random direction

# Game loop
running = True
game_over = False
while running:
    screen.fill((0, 0, 0))  # Clear the screen

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_SPACE:  # Reset game on spacebar press
                reset_game()

    if not game_over:
        # Move player
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player_x > 0:  # Left arrow or A key
            player_x -= player_speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player_x < SCREEN_WIDTH - player_width:  # Right arrow or D key
            player_x += player_speed

        # Spawn enemies randomly
        if random.randint(1, 100) == 1:
            spawn_enemy()

        # Move enemies randomly
        for enemy in enemies[:]:
            enemy[0] += enemy[2] * enemy_speed  # Move left or right
            enemy[1] += enemy_speed  # Move down
            if enemy[0] < 0 or enemy[0] > SCREEN_WIDTH - enemy_width:
                enemy[2] *= -1  # Reverse direction
            if enemy[1] > SCREEN_HEIGHT:
                enemies.remove(enemy)

        # Automatically shoot bullets
        if len(bullets) < 5:  # Limit the number of bullets on screen
            bullet_x = player_x + player_width // 2 - bullet_width // 2
            bullet_y = player_y
            bullets.append([bullet_x, bullet_y])

        # Move bullets and check for collisions
        for bullet in bullets[:]:
            bullet[1] -= bullet_speed
            if bullet[1] < 0:
                bullets.remove(bullet)
            else:
                for enemy in enemies[:]:
                    if (bullet[0] < enemy[0] + enemy_width and
                        bullet[0] + bullet_width > enemy[0] and
                        bullet[1] < enemy[1] + enemy_height and
                        bullet[1] + bullet_height > enemy[1]):
                        bullets.remove(bullet)
                        explosions.append([enemy[0] + enemy_width // 2, enemy[1] + enemy_height // 2])
                        enemies.remove(enemy)
                        break

        # Check for player collision with enemies
        for enemy in enemies[:]:
            if (player_x < enemy[0] + enemy_width and
                player_x + player_width > enemy[0] and
                player_y < enemy[1] + enemy_height and
                player_y + player_height > enemy[1]):
                explosions.append([player_x + player_width // 2, player_y + player_height // 2])
                game_over = True

        # Draw everything
        draw_player(player_x, player_y)
        for enemy in enemies:
            draw_enemy(enemy[0], enemy[1])
        for bullet in bullets:
            draw_bullet(bullet[0], bullet[1])
        for explosion in explosions[:]:
            draw_explosion(explosion[0], explosion[1])
            explosions.remove(explosion)  # Remove explosion after drawing

    else:
        # Game over screen
        font = pygame.font.SysFont(None, 74)
        text = font.render("GAME OVER", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 50))
        text = font.render("Press SPACE to try again", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 + 50))

    # Update the display
    pygame.display.update()
    clock.tick(60)  # 60 FPS

# Quit Pygame
pygame.quit()
sys.exit()