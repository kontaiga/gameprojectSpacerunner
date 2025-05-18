import random
import pygame
import os
from pgzero.keyboard import keys

WIDTH = 800
HEIGHT = 600


PLAYER_SPEED = 5
BASE_ENEMY_SPEED = 3
NUM_ENEMIES = 2
INITIAL_LIVES = 3
rotating_enemies = []
pending_rotating_enemies = []  # Gecikmeli eklenecek düşmanlar
enemy_spawn_timer = 0  # Zamanlayıcı
level_damage_taken = False
perfect_level_streak = 0
life_up_sound = pygame.mixer.Sound("music/powerup.mp3")

STATE_OPTIONS = "options"
STATE_EXIT = "exit"
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_LOST = "lost"
menu_selection = 0
menu_options = ["Start", "Options", "Exit"]
options_selection = 0
options_list = ["Music Volume", "Screen Size"]
music_volume = 0.5  # 0.0 ile 1.0 arası
screen_size_index = 0
screen_sizes = [(800, 600), (1024, 768), (1280, 720)]

score = 0
lives = INITIAL_LIVES
best_score = 0
game_state = STATE_MENU

def apply_screen_size(index):
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = screen_sizes[index]
    screen.surface = pygame.display.set_mode((WIDTH, HEIGHT))

def load_best_score():
    global best_score
    if os.path.exists("highscore.txt"):
        with open("highscore.txt", "r") as f:
            try:
                best_score = int(f.read())
            except:
                best_score = 0
    else:
        best_score = 0
def save_best_score():
    with open("highscore.txt", "w") as f:
        f.write(str(best_score))

load_best_score()

sheet = pygame.image.load("images/spritesheet3.png").convert_alpha()
SW, SH = sheet.get_width(), sheet.get_height()
FW = SW // 7
FH = SH // 6
player_frames = {
    "idle": [],        # sağa bakan durma
    "up": [],          # sağa bakan yukarı hareket
    "down": [],        # sağa bakan aşağı hareket
    "left_idle": [],   # sola bakan durma
    "left_up": [],     # sola bakan yukarı hareket
    "left_down": []    # sola bakan aşağı hareket
}

for col in range(7):
    rect = pygame.Rect(col * FW, 0 * FH, FW, FH)
    img = pygame.transform.scale(sheet.subsurface(rect), (64, 64))
    if col == 0:
        player_frames["idle"].append(img)
    elif 1 <= col <= 3:
        player_frames["down"].append(img)
    else:
        player_frames["up"].append(img)

for col in range(7):
    rect = pygame.Rect(col * FW, 4 * FH, FW, FH)
    img = pygame.transform.scale(sheet.subsurface(rect), (64, 64))
    if col == 0:
        player_frames["left_idle"].append(img)
    elif 1 <= col <= 3:
        player_frames["left_up"].append(img)    # sol yukarı animasyonlar burada
    else:
        player_frames["left_down"].append(img)  # sol aşağı animasyonlar burada

explo_frames_right = []
explo_frames_left = []


for col in range(7):
    # Satır 3: sağa bakan patlama
    rect = pygame.Rect(col * FW, 3 * FH, FW, FH)
    img = pygame.transform.scale(sheet.subsurface(rect), (128, 128))
    explo_frames_right.append(img)

    # Satır 5: sola bakan patlama
    rect2 = pygame.Rect(col * FW, 5 * FH, FW, FH)
    img2 = pygame.transform.scale(sheet.subsurface(rect2), (128, 128))
    explo_frames_left.append(img2)

heart_sheet = pygame.image.load("images/heart.png").convert_alpha()
HW = heart_sheet.get_width() // 2
HH = heart_sheet.get_height()
heart_full = heart_sheet.subsurface(pygame.Rect(0, 0, HW, HH))
heart_empty = heart_sheet.subsurface(pygame.Rect(HW, 0, HW, HH))

HEART_DRAW_SIZE = 40
HEART_SPACING = 10
HEART_MARGIN = 10

def draw_lives(current_lives):
    for i in range(INITIAL_LIVES):
        img = heart_full if i < current_lives else heart_empty
        img = pygame.transform.scale(img, (HEART_DRAW_SIZE, HEART_DRAW_SIZE))
        x = WIDTH - HEART_MARGIN - (i + 1) * HEART_DRAW_SIZE - i * HEART_SPACING
        y = HEART_MARGIN
        screen.blit(img, (x, y))

clock = pygame.time.Clock()

class AnimatedPlayer:
    def __init__(self, pos):
        self.x, self.y = pos
        self.direction = "right"  # sağa mı sola mı bakıyor?
        self.state = "idle"
        self.frames = player_frames
        self.index = 0
        self.delay = 6
        self.counter = 0
        self.w = 64
        self.h = 64


    def update(self):
        old_state = self.state
        moving = False
        clock.tick(60)

        # Hareket kontrolü
        if keyboard.left and self.x > 20:
            self.x -= PLAYER_SPEED
            self.direction = "left"
            moving = True
        if keyboard.right and self.x < WIDTH - 20:
            self.x += PLAYER_SPEED
            self.direction = "right"
            moving = True
        if keyboard.up and self.y > 20:
            self.y -= PLAYER_SPEED
            moving = True
            self.state = "up" if self.direction == "right" else "left_up"
        elif keyboard.down and self.y < HEIGHT - 20:
            self.y += PLAYER_SPEED
            moving = True
            self.state = "down" if self.direction == "right" else "left_down"
        elif moving:
            # yukarı/aşağı harici hareket
            self.state = "idle" if self.direction == "right" else "left_idle"

        if not moving:
            self.state = "idle" if self.direction == "right" else "left_idle"

            # Eğer yukarı/aşağı hareket ediliyorsa sabit kare göster
        if self.state in ["down", "up", "left_down", "left_up"]:
            self.index = 2  # Sabit kare
            self.counter = 0
            return

            # Durma ya da sağa/sola yatay hareket animasyon döngüsü
        if self.state != old_state:
            self.index = 0
            self.counter = 0
            return

        self.counter += 1
        if self.counter >= self.delay:
            self.counter = 0
            self.index = (self.index + 1) % len(self.frames[self.state])


    def draw(self):
        img = self.frames[self.state][self.index]
        screen.blit(img, (self.x - self.w // 2, self.y - self.h // 2))

    def rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

class Explosion:
    def __init__(self, pos, direction):
        self.frames = explo_frames_right if direction == "right" else explo_frames_left
        self.index = 0
        self.delay = 5
        self.count = 0
        self.x, self.y = pos
        self.finished = False

    def update(self):
        if self.finished:
            return
        self.count += 1
        if self.count >= self.delay:
            self.count = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.finished = True

    def draw(self):
        if self.finished:
            return
        img = self.frames[self.index]
        w, h = img.get_width(), img.get_height()
        screen.blit(img, (self.x - w // 2, self.y - h // 2))

ENEMY_IMAGES = []

for i in range(1, 11):
    path = f"images/damaged ship parts/part{i}.png"
    image = pygame.image.load(path).convert_alpha()
    ENEMY_IMAGES.append(image)

class Meteor:
    def __init__(self):
        self.x = random.randint(200, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.scale = random.uniform(0.9, 1.2) * 10

        self.original_img = random.choice(ENEMY_IMAGES)
        w, h = self.original_img.get_size()
        self.scale = random.uniform(0.9, 1.2) * 1.5

        # Yeni boyutları hesapla
        scaled_w = int(w * self.scale)
        scaled_h = int(h * self.scale)
        self.img = pygame.transform.scale(self.original_img, (scaled_w, scaled_h))

        self.width = scaled_w
        self.height = scaled_h
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def update(self, speed):
        self.y += speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(200, WIDTH - 50)
        self.rect.topleft = (self.x - self.width // 2, self.y - self.height // 2)

    def draw(self):
        screen.blit(self.img, (self.x - self.width // 2, self.y - self.height // 2))

    def colliderect(self, player_rect):
        return self.rect.colliderect(player_rect)


class RotatingEnemy:
    def __init__(self, x=None, y=None):
        ship_names = ["mainship1.png", "mainship2.png", "mainship3.png", "mainship4.png", "mainship5.png"]
        chosen_ship = random.choice(ship_names)
        path = os.path.join("images", "rotatingenemies", chosen_ship)
        self.original_img = pygame.image.load(path).convert_alpha()

        self.scale = 2.0
        w, h = self.original_img.get_size()
        new_size = (int(w * self.scale), int(h * self.scale))
        self.original_img = pygame.transform.scale(self.original_img, new_size)

        self.img = self.original_img.copy()
        self.width, self.height = new_size
        self.x = x if x is not None else random.randint(200, WIDTH - 100)
        self.y = y if y is not None else random.randint(-100, -50)

        speed_magnitude = random.uniform(0.01, 0.1)
        self.rotation_speed = speed_magnitude if random.random() < 0.5 else -speed_magnitude
        if -0.5 < self.rotation_speed < 0.5:
            self.rotation_speed = 0.5 if random.random() < 0.5 else -0.5

        self.angle = 0

        # Hitbox ayarları (görselin ortasına göre)
        shrink_ratio = 0.4
        self.hitbox_width = int(self.width * shrink_ratio)
        self.hitbox_height = int(self.height * shrink_ratio)
        self.rect = pygame.Rect(0, 0, self.hitbox_width, self.hitbox_height)
        self.rect.center = (self.x, self.y)


    def update(self, speed):
        self.y += speed * 0.8
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(200, WIDTH - 100)

        self.angle = (self.angle + self.rotation_speed) % 360
        self.img = pygame.transform.rotate(self.original_img, self.angle)

        # Görselin merkezine göre konumlandırma
        img_rect = self.img.get_rect(center=(self.x, self.y))

        # Hitbox'ın merkezini düşmanın merkeziyle eşleştir
        self.rect.center = (self.x, self.y)

    def draw(self):
        screen.blit(self.img, self.img.get_rect(center=(self.x, self.y)))
        # İstersen debug için hitbox'ı çiz:
        # pygame.draw.rect(screen.surface, (255, 0, 0), self.rect, 2)

    def colliderect(self, player_rect):
        return self.rect.colliderect(player_rect)

def spawn_rotating_enemy_not_too_close(existing_enemies, min_distance=250):
    attempts = 0
    while attempts < 100:
        x = random.randint(200, WIDTH - 100)
        y = random.randint(50, HEIGHT - 100)
        too_close = any(
            ((x - e.x) ** 2 + (y - e.y) ** 2) ** 0.5 < min_distance
            for e in existing_enemies
        )
        if not too_close:
            return RotatingEnemy(x, y)
        attempts += 1
    return RotatingEnemy(x, y)  # fallback

player = AnimatedPlayer((50, HEIGHT // 2))
enemies = []
explosions = []

def spawn_enemies():
    enemies.clear()
    attempts = 0
    while len(enemies) < NUM_ENEMIES and attempts < 100:
        new_meteor = Meteor()
        too_close = any(
            abs(new_meteor.x - e.x) < 80 and abs(new_meteor.y - e.y) < 80 for e in enemies
        )
        if not too_close:
            enemies.append(new_meteor)
        attempts += 1


def start_game():
    global score, lives, game_state, rotating_enemies
    global perfect_level_streak
    global level_damage_taken, perfect_level_streak
    rotating_enemies = []
    for _ in range(2):
        new_enemy = spawn_rotating_enemy_not_too_close(rotating_enemies)
        rotating_enemies.append(new_enemy)
    score = 0
    lives = INITIAL_LIVES
    game_state = STATE_PLAYING
    player.x, player.y = 50, HEIGHT // 2
    spawn_enemies()

    rotating_enemies = []
    attempts = 0
    while len(rotating_enemies) < 2 and attempts < 100:
        new_enemy = RotatingEnemy()
        too_close = any(
            ((new_enemy.x - e.x) ** 2 + (new_enemy.y - e.y) ** 2) ** 0.5 < 250
            for e in rotating_enemies
        )
        if not too_close:
            rotating_enemies.append(new_enemy)
        attempts += 1
    level_damage_taken = False
    perfect_level_streak = 0

MAX_ROTATING_ENEMIES = 2

def next_level():
    global score, lives, level_damage_taken, perfect_level_streak

    # Sadece ihtiyaç varsa yeni düşman ekle (beklemeli)
    while len(rotating_enemies) + len(pending_rotating_enemies) < MAX_ROTATING_ENEMIES:
        pending_rotating_enemies.append({
            "delay": random.randint(30, 120),
            "enemy": spawn_rotating_enemy_not_too_close(rotating_enemies)
        })

    score += 10

    if not level_damage_taken:
        perfect_level_streak += 1
        if perfect_level_streak >= 3 and lives < INITIAL_LIVES:
            lives += 1
            perfect_level_streak = 0
            life_up_sound.play()
    else:
        perfect_level_streak = 0  # Hasar aldıysa seriyi boz

    level_damage_taken = False  # Yeni seviye başı
    player.x, player.y = 50, HEIGHT // 2
    spawn_enemies()

def update():
    global game_state, lives, best_score, level_damage_taken, perfect_level_streak
    if len(rotating_enemies) + len(pending_rotating_enemies) >= MAX_ROTATING_ENEMIES:
        pending_rotating_enemies[:] = pending_rotating_enemies[:MAX_ROTATING_ENEMIES - len(rotating_enemies)]
    if pending_rotating_enemies:
        for item in pending_rotating_enemies[:]:
            item["delay"] -= 1
            if item["delay"] <= 0:
                # Yeni enemy konumu mevcutlara göre kontrol edilsin
                too_close = any(
                    ((item["enemy"].x - e.x) ** 2 + (item["enemy"].y - e.y) ** 2) ** 0.5 < 200
                    for e in rotating_enemies
                )
                if not too_close:
                    rotating_enemies.append(item["enemy"])
                    pending_rotating_enemies.remove(item)
                else:
                    # Yakınsa yeniden konumlandır ve gecikmeyi tekrar ayarla
                    item["enemy"] = RotatingEnemy()
                    item["delay"] = random.randint(30, 120)
    for ex in explosions:
        ex.update()
    explosions[:] = [ex for ex in explosions if not ex.finished]
    if game_state != STATE_PLAYING:
        return

    player.update()
    speed = BASE_ENEMY_SPEED + (score // 10)
    for e in enemies:
        e.update(speed)
    for e in enemies:
        if e.colliderect(player.rect()):
            sounds.hit.play()
            explosions.append(Explosion((player.x, player.y), player.direction))
            level_damage_taken = True
            perfect_level_streak = 0
            lives -= 1
            if lives <= 0:
                if score > best_score:
                    best_score = score
                    save_best_score()
                game_state = STATE_LOST
            else:
                player.x, player.y = 50, HEIGHT // 2
            break
    if player.x >= WIDTH - 20:
        sounds.win.play()
        next_level()
    for ex in explosions:
        ex.update()
    explosions[:] = [ex for ex in explosions if not ex.finished]

    for r_enemy in rotating_enemies:
        r_enemy.update(speed)
        if r_enemy.colliderect(player.rect()):
            sounds.hit.play()
            explosions.append(Explosion((player.x, player.y), player.direction))
            level_damage_taken = True
            perfect_level_streak = 0
            lives -= 1
            if lives <= 0:
                if score > best_score:
                    best_score = score
                    save_best_score()
                game_state = STATE_LOST
            else:
                player.x, player.y = 50, HEIGHT // 2
            break

def restart_game():
    global game_state, score, lives, rotating_enemies, pending_rotating_enemies
    global level_damage_taken, perfect_level_streak

    score = 0
    lives = INITIAL_LIVES
    player.x, player.y = 50, HEIGHT // 2
    rotating_enemies.clear()
    pending_rotating_enemies.clear()
    explosions.clear()
    spawn_enemies()

    for _ in range(2):
        new_enemy = spawn_rotating_enemy_not_too_close(rotating_enemies)
        rotating_enemies.append(new_enemy)

    level_damage_taken = False
    perfect_level_streak = 0
    game_state = STATE_PLAYING

def on_key_down(key):
    global game_state
    global menu_selection, options_selection
    global music_volume, screen_size_index

    if game_state == STATE_MENU:
        if key == keys.UP:
            menu_selection = (menu_selection - 1) % len(menu_options)
        elif key == keys.DOWN:
            menu_selection = (menu_selection + 1) % len(menu_options)
        elif key == keys.RETURN:
            selection = menu_options[menu_selection]
            if selection == "Start":
                start_game()
            elif selection == "Options":
                game_state = STATE_OPTIONS
            elif selection == "Exit":
                pygame.quit()
                exit()

    elif game_state == STATE_OPTIONS:
        if key == keys.UP:
            options_selection = (options_selection - 1) % len(options_list)
        elif key == keys.DOWN:
            options_selection = (options_selection + 1) % len(options_list)
        elif key == keys.LEFT:
            if options_list[options_selection] == "Music Volume":
                music_volume = max(0.0, music_volume - 0.1)
                pygame.mixer.music.set_volume(music_volume)
            elif options_list[options_selection] == "Screen Size":
                screen_size_index = (screen_size_index - 1) % len(screen_sizes)
                apply_screen_size(screen_size_index)
        elif key == keys.RIGHT:
            if options_list[options_selection] == "Music Volume":
                music_volume = min(1.0, music_volume + 0.1)
                pygame.mixer.music.set_volume(music_volume)
            elif options_list[options_selection] == "Screen Size":
                screen_size_index = (screen_size_index + 1) % len(screen_sizes)
                apply_screen_size(screen_size_index)
        elif key == keys.ESCAPE:
            game_state = STATE_MENU

    elif game_state == STATE_LOST:
        if key == keys.R:
            restart_game()

    elif key == keys.P:
        if game_state == STATE_PLAYING:
            game_state = STATE_PAUSED
        elif game_state == STATE_PAUSED:
            game_state = STATE_PLAYING
def draw_menu():
    screen.draw.text("Main Menu", center=(WIDTH // 2, 100), fontsize=60, color="white")
    for i, option in enumerate(menu_options):
        color = "yellow" if i == menu_selection else "white"
        screen.draw.text(option, center=(WIDTH // 2, 200 + i * 50), fontsize=40, color=color)

def draw_options():
    screen.draw.text("Options", center=(WIDTH // 2, 100), fontsize=60, color="white")
    for i, option in enumerate(options_list):
        color = "yellow" if i == options_selection else "white"
        value = ""
        if option == "Music Volume":
            value = f"{int(music_volume * 100)}%"
        elif option == "Screen Size":
            value = f"{screen_sizes[screen_size_index][0]}x{screen_sizes[screen_size_index][1]}"
        screen.draw.text(f"{option}: {value}", center=(WIDTH // 2, 200 + i * 50), fontsize=40, color=color)

def draw():
    screen.clear()
    screen.blit("background", (0, 0))
    if game_state == STATE_MENU:
        draw_menu()
        return
    elif game_state == STATE_OPTIONS:
        draw_options()
        return
    draw_lives(lives)

    player.draw()
    for e in enemies:
        e.draw()
    for ex in explosions:
        ex.draw()
    for r_enemy in rotating_enemies:
        r_enemy.draw()

    # Karanlık arka plan katmanı (kazanınca veya kaybedince)
    if game_state in [STATE_LOST, STATE_PAUSED]:
        dark_overlay = pygame.Surface((WIDTH, HEIGHT))
        dark_overlay.set_alpha(150)  # Şeffaflık: 0-255
        dark_overlay.fill((0, 0, 0))
        screen.surface.blit(dark_overlay, (0, 0))

    if game_state == STATE_MENU:
        screen.draw.text("Hos geldiniz!", center=(WIDTH // 2, HEIGHT // 2 - 50), fontsize=60, color="white")
        screen.draw.text("Baslamak icin 'SPACE' tusuna basiniz", center=(WIDTH // 2, HEIGHT // 2), fontsize=30, color="white")
        return

    if game_state == STATE_LOST:
        screen.draw.text(f"Kaybettiniz! Skor: {score}", center=(WIDTH // 2, HEIGHT // 2), fontsize=60, color="red")
        screen.draw.text("Tekrar oynamak icin 'R' tusuna basiniz", center=(WIDTH // 2, HEIGHT // 2 + 50), fontsize=30, color="white")
        screen.draw.text(f"En iyi Skor: {best_score}", center=(WIDTH // 2, HEIGHT // 2 + 100), fontsize=30, color="white")
    elif game_state == STATE_PAUSED:
        screen.draw.text("Oyun Duraklatildi", center=(WIDTH // 2, HEIGHT // 2), fontsize=60, color="orange")
        screen.draw.text(f"Skor: {score}", topleft=(10, 10), fontsize=30, color="white")
        screen.draw.text(f"En iyi Skor: {best_score}", topleft=(10, 50), fontsize=30, color="white")
    else:
        screen.draw.text(f"Skor: {score}", topleft=(10, 10), fontsize=30, color="white")
        screen.draw.text(f"En iyi Skor: {best_score}", topleft=(10, 50), fontsize=30, color="white")



music.play("bgmusic.mp3")
