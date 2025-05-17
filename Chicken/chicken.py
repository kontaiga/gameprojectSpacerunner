import random
import pygame
from pgzero.keyboard import keys

WIDTH = 800
HEIGHT = 600


player = Actor('player', (50, HEIGHT // 2))

enemies = []
for _ in range(5):
    x = random.randint(200, WIDTH - 50)
    y = random.randint(50, HEIGHT - 50)
    enemy = Actor('enemy', (x, y))
    enemies.append(enemy)

score = 0
game_state = "playing"


def check_collision(player, enemies):
    player_rect = pygame.Rect(player.x - 10, player.y - 10, 20, 20)

    for enemy in enemies:
        enemy_rect = pygame.Rect(enemy.x - 15, enemy.y - 15, 30, 30)
        if player_rect.colliderect(enemy_rect):
            return True
    return False


def update():
    global game_state

    if game_state != "playing":
        return

    if keyboard.up and player.y > 20:
        player.y -= 5
    if keyboard.down and player.y < HEIGHT - 20:
        player.y += 5
    if keyboard.left and player.x > 20:
        player.x -= 5
    if keyboard.right and player.x < WIDTH - 20:
        player.x += 5

    for enemy in enemies:
        enemy.y += 3
        if enemy.y > HEIGHT:
            enemy.y = 0
            enemy.x = random.randint(200, WIDTH - 50)

    if check_collision(player, enemies):
        game_state = "lost"

    if player.x >= WIDTH - 20:
        game_state = "won"

def on_key_down(key):
    global game_state
    if key == keys.R and (game_state == "won" or game_state == "lost"):
        reset_game()

def draw():
    screen.clear()
    screen.fill((50, 150, 50))

    player.draw()

    for enemy in enemies:
        enemy.draw()

    if game_state == "won":
        screen.draw.text("Kazandınız!", center=(WIDTH // 2, HEIGHT // 2), fontsize=60, color="yellow")
        screen.draw.text("Tekrar oynamak için 'R' tuşuna basın", center=(WIDTH // 2, HEIGHT // 2 + 50), fontsize=30, color="white")
    elif game_state == "lost":
        screen.draw.text("Kaybettiniz!", center=(WIDTH // 2, HEIGHT // 2), fontsize=60, color="red")
        screen.draw.text("Tekrar oynamak için 'R' tuşuna basın", center=(WIDTH // 2, HEIGHT // 2 + 50), fontsize=30, color="white")

def reset_game():
    global score, game_state, player, enemies

    score = 0
    game_state = "playing"

    player.x = 50
    player.y = HEIGHT // 2

    enemies.clear()
    for _ in range(5):
        x = random.randint(200, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        enemy = Actor('enemy', (x, y))
        enemies.append(enemy)
