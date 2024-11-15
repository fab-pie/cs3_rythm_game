import pygame
import time
import random
import csv
import datetime
import os
import librosa

import numpy as np

pygame.init()

# Upload musics
musics = [
    ('Lofi.wav', 'Tutorial - Lofi', 0.3),
    ('Next_To_You.wav', 'Easy - Next To You', 0.5),
    ('Warriors.wav', 'Intermediate - Warriors', 0.75),
    ('Beat_Saber.wav', 'Hard - Beat Saber', 0.80),
    ('Last_Friday_Night.wav', 'Ultra Hardcore - Hardstyle LFN', 1.1),
    ('Camelia.wav', 'GOD - Camelia', 1.4)
]

# For Normal mode
def adjust_scroll_speed_to_music(level_name, base_speed):
    scroll_speed_levels = {
        'Tutorial - Lofi': 3,
        'Easy - Next To You': 5,
        'Intermediate - Warriors': 8,
        'Hard - Beat Saber': 12,
        'Ultra Hardcore - Hardstyle LFN': 15,
        'GOD - Camelia': 18
    }
    return scroll_speed_levels.get(level_name, base_speed)

# Screen parameters
screen = pygame.display.set_mode((800, 850))
clock = pygame.time.Clock()
pygame.display.set_caption("My Rhythm Game")

PLATFORM_COLOR = (200, 100, 50)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 850

class Platform:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, offset_y):
        self.rect.y += offset_y
        pygame.draw.rect(screen, PLATFORM_COLOR, self.rect, border_radius=10)

# Player class
class Player:
    # Spawn parameters
    def __init__(self):
        self.x = 350
        self.y = 600
        self.width = 100
        self.height = 100
        self.velocity_y = 0
        self.is_jumping = False
        self.img = pygame.transform.scale(pygame.image.load('rayman.png'), (self.width, self.height))
        self.start_time = None 
        self.first_jump = False

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = -25
            self.is_jumping = True
            if not self.first_jump:
                self.first_jump = True
                self.start_time = time.time()
                pygame.mixer.music.play(-1)

    def move(self, val):
        self.x += val

    # Gravity, fast fall, left to right...
    def update(self, platforms):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            self.velocity_y += 5
        else:
            self.velocity_y += 1

        self.y += self.velocity_y
        self.check_platform_collisions(platforms)

        if self.y >= 750:
            self.lost()
            return False
        
        if self.x > SCREEN_WIDTH:
            self.x = -self.width
        elif self.x + self.width < 0:
            self.x = SCREEN_WIDTH
        
        screen.blit(self.img, (self.x, self.y))
        return True

    # Check if player hit platform
    def check_platform_collisions(self, platforms):
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for platform in platforms:
            if player_rect.colliderect(platform.rect) and self.velocity_y > 0:
                if self.y + self.height <= platform.rect.top + self.velocity_y:
                    self.y = platform.rect.top - self.height
                    self.velocity_y = 0
                    self.is_jumping = False
                    break

    def lost(self):
        pygame.mixer.music.stop()
        return False

    def get_time_alive(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0 


def generate_platforms():
    platforms = [
        Platform(200, 400, 150, 20),
        Platform(600, 200, 150, 20),
        Platform(300, 100, 150, 20),
        Platform(520, 590, 150, 20),
        Platform(250, 740, 300, 20),
        Platform(20, -100, 150, 20)
    ]
    return platforms

def get_audio_duration(music_file):
    sound = pygame.mixer.Sound(music_file)
    return sound.get_length()

# Allow to have rythm mode since you have the tempos for segment of the music
def calculate_tempos_for_music(music_file, segment_duration=0.25):
    y, sr = librosa.load(music_file, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    tempos = []
    for segment_start in range(0, int(duration), int(segment_duration)):
        start_sample = int(segment_start * sr)
        end_sample = int((segment_start + segment_duration) * sr)
        segment = y[start_sample:end_sample]
        
        if len(segment) == 0:
            tempo = 120
        else:
            tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0]
        tempos.append(tempo)
    
    return tempos

# Show menu, different level, mode, name...
def show_start_menu(selected_music_index, player_name, selected_mode):
    font = pygame.font.SysFont(None, 40)
    screen.fill((0, 0, 0))

    title_text = font.render("My Rhythm Game", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 5))

    instructions_text = font.render("Tap on 'Enter' to start", True, (255, 255, 255))
    screen.blit(instructions_text, (SCREEN_WIDTH // 2 - instructions_text.get_width() // 2, SCREEN_HEIGHT // 2))

    name_text = font.render(f"Name : {player_name}", True, (255, 255, 255))
    screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

    for i, (_, title, _) in enumerate(musics):
        color = (0, 255, 0) if i == selected_music_index else (255, 255, 255)
        music_text = font.render(title, True, color)
        screen.blit(music_text, (SCREEN_WIDTH // 2 - music_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50 + i * 40))

    selected_mode = selected_mode
    mode_text = font.render(f"Mode: {selected_mode}", True, (255, 255, 255))
    screen.blit(mode_text, (SCREEN_WIDTH // 2 - mode_text.get_width() // 2, SCREEN_HEIGHT - 100))

    pygame.display.flip()

# Screen show after loosing with score and leaderboard
def show_game_over(score, player_name, level_name, mode):
    font = pygame.font.SysFont(None, 60)
    small_font = pygame.font.SysFont(None, 40)

    game_over_text = font.render("Game Over!", True, (255, 0, 0))
    score_text = font.render(f"{player_name} - Score: {score} secondes", True, (255, 255, 255))

    screen.fill((0, 0, 0))
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 4))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 3))

    leaderboard = load_all_game_data()
    key = (level_name, mode)
    top_scores = leaderboard.get(key, [])

    leaderboard_title = small_font.render("Top Scores", True, (255, 255, 0))
    screen.blit(leaderboard_title, (SCREEN_WIDTH // 2 - leaderboard_title.get_width() // 2, SCREEN_HEIGHT // 2))

    y_offset = SCREEN_HEIGHT // 2 + 40
    for rank, entry in enumerate(top_scores, start=1):
        player = entry["player_name"]
        top_score = entry["score"]
        score_entry_text = small_font.render(f"{rank}. {player}: {top_score} secondes", True, (200, 200, 200))
        screen.blit(score_entry_text, (SCREEN_WIDTH // 2 - score_entry_text.get_width() // 2, y_offset))
        y_offset += 30

    pygame.display.flip()
    pygame.time.wait(5000)

# Same but if winning
def show_level_cleared(player_name, score, level_name, mode):
    font = pygame.font.SysFont(None, 60)
    small_font = pygame.font.SysFont(None, 40)

    cleared_text = font.render("Clear!", True, (0, 255, 0))
    score_text = font.render(f"{player_name} - Score: {score} secondes", True, (255, 255, 255))

    screen.fill((0, 0, 0))
    screen.blit(cleared_text, (SCREEN_WIDTH // 2 - cleared_text.get_width() // 2, SCREEN_HEIGHT // 3))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))

    leaderboard = load_all_game_data()
    key = (level_name, mode)
    top_scores = leaderboard.get(key, [])

    leaderboard_title = small_font.render("Top Scores", True, (255, 255, 0))
    screen.blit(leaderboard_title, (SCREEN_WIDTH // 2 - leaderboard_title.get_width() // 2, SCREEN_HEIGHT // 2-90))

    y_offset = SCREEN_HEIGHT // 2 + 40
    for rank, entry in enumerate(top_scores, start=1):
        player = entry["player_name"]
        top_score = entry["score"]
        score_entry_text = small_font.render(f"{rank}. {player}: {top_score} secondes", True, (200, 200, 200))
        screen.blit(score_entry_text, (SCREEN_WIDTH // 2 - score_entry_text.get_width() // 2, y_offset))
        y_offset += 30

    pygame.display.flip()
    pygame.time.wait(3000)

# Take data from every csv made to have a leaderboard
def load_all_game_data():
    leaderboard = {}

    for filename in os.listdir():
        if filename.endswith(".csv"):
            try:
                with open(filename, mode="r", newline="") as file:
                    reader = csv.DictReader(file, delimiter=";")
                    for row in reader:
                        level = row["level"]
                        score = int(row["score"]) if "score" in row else None
                        mode = row["mode"]
                        player_name = os.path.splitext(filename)[0]
                        is_clear = row.get("clear", "False") == "True"
                        key = (level, mode)                        
                        if key not in leaderboard:
                            leaderboard[key] = []
                        if is_clear:
                            leaderboard[key].append({"player_name": player_name, "is_clear": True})
                        else:
                            leaderboard[key].append({"player_name": player_name, "score": score})

            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {filename}: {e}")

    for key in leaderboard:
        leaderboard[key] = sorted(leaderboard[key], key=lambda x: x.get("score", 0), reverse=True)[:3]

    return leaderboard

# General leaderboard
def show_leaderboard():
    font = pygame.font.SysFont(None, 40)

    leaderboard = load_all_game_data()   
    screen.fill((0, 0, 0))   
    y_offset = 50 
    title_text = font.render("General Leaderboard", True, (255, 255, 0))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, y_offset))
    y_offset += 60

    for (level, mode), top_scores in leaderboard.items():
        level_mode_text = font.render(f"Level: {level} | Mode: {mode}", True, (255, 255, 255))
        screen.blit(level_mode_text, (50, y_offset))
        y_offset += 40

        for rank, entry in enumerate(top_scores, start=1):
            player_name = entry["player_name"]
            score = entry["score"]
            score_text = font.render(f"{rank}. {player_name}: {score} secondes", True, (200, 200, 200))
            screen.blit(score_text, (70, y_offset))
            y_offset += 30

        y_offset += 20 

        if y_offset > SCREEN_HEIGHT - 50:
            break

    pygame.display.flip()
    pygame.time.wait(5000)  

# Load only your data so that you have your personal best score for each level
def load_game_data(player_name):
    filename = f"{player_name}.csv"
    level_data = {}  

    try:
        with open(filename, mode="r", newline="") as file:
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                level = row["level"]
                score = int(row["score"])
                mode = row["mode"]
                cleared = row["cleared"] == "Yes"
                
                # Si le niveau existe déjà, on garde seulement le meilleur score
                if (level, mode) not in level_data or score > level_data[level, mode]["best_score"]:
                    level_data[level, mode] = {"best_score": score, "cleared": cleared}
    except FileNotFoundError:
        print(f"No data file found for {player_name}.")

    return level_data

# Create a csv file to save the data
def save_game_data(player_name, level, score, mode, level_cleared):
    filename = f"{player_name}.csv"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file, delimiter=";")

        if not file_exists:
            writer.writerow(["level", "date", "score", "mode", "cleared"])

        writer.writerow([level, now, score, mode, "Yes" if level_cleared else "No"])
    print(f"Data saved for {player_name} in {filename}")

# Game loop use different function to make the game really work as it should be, also link to different pages, create loading screen, pause menu...
def game_loop(music_file, player_name, level_name, mode):
    screen.fill((0, 0, 0))
    font = pygame.font.SysFont(None, 50)
    loading_text = font.render("Chargement...", True, (255, 255, 255))
    screen.blit(loading_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    segment_duration = 1.0
    tempos = calculate_tempos_for_music(music_file, segment_duration)
    
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.play()
    
    duration = get_audio_duration(music_file)
    link = Player()
    running = True
    platforms = generate_platforms()
    game_started = False
    is_paused = False
    pause_start_time = 0
    total_pause_duration = 0
    level_cleared = False
    scroll_speed_normal = adjust_scroll_speed_to_music(level_name, base_speed=5)
    start_time = time.time()

    
    speed_multiplier = None
    for music in musics:
        if music[1] == level_name:
            speed_multiplier = music[2] 
            break

    while running:
        current_time = time.time() - start_time - total_pause_duration
        segment_index = int(current_time // segment_duration)
        
        if mode == "Normal":
            scroll_speed = scroll_speed_normal
            
        else:
            if segment_index < len(tempos):
                if speed_multiplier is not None:
                    scroll_speed = tempos[segment_index] * speed_multiplier / 12
                else:
                    scroll_speed = scroll_speed_normal
            else:
                scroll_speed = scroll_speed_normal

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    link.jump()
                    if not game_started and link.first_jump:
                        game_started = True
                elif event.key == pygame.K_b:
                    if is_paused:
                        is_paused = False
                        total_pause_duration += time.time() - pause_start_time
                        pygame.mixer.music.unpause()
                    else:
                        is_paused = True
                        pause_start_time = time.time()
                        pygame.mixer.music.pause()

        if is_paused:
            continue

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            link.move(-10)
        if keys[pygame.K_RIGHT]:
            link.move(10)

        screen.fill((0, 0, 0))

        elapsed_time = link.get_time_alive() - int(total_pause_duration)
        
        if elapsed_time >= duration:
            level_cleared = True
            break

        font = pygame.font.SysFont(None, 40)
        score_text = font.render(f"Score: {elapsed_time} secondes", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        if game_started:
            for platform in platforms:
                platform.draw(scroll_speed)

            platforms = [p for p in platforms if p.rect.top < SCREEN_HEIGHT]

            if platforms and platforms[-1].rect.top > 200:
                new_y = platforms[-1].rect.top - 200
                num_platforms = random.randint(1, 3)
                for _ in range(num_platforms):
                    x = random.randint(50, SCREEN_WIDTH - 200)
                    new_platform = Platform(x, new_y, 150, 20)
                    platforms.append(new_platform)

        if not link.update(platforms):
            save_game_data(player_name, level_name, elapsed_time, mode, False)
            show_game_over(elapsed_time, player_name, level_name, mode)
            pygame.mixer.music.stop()
            return True

        pygame.display.flip()
        clock.tick(60)
 
    if level_cleared:
        save_game_data(player_name, level_name, elapsed_time, mode, True)
        show_level_cleared(player_name, elapsed_time, level_name, mode)
        pygame.mixer.music.stop()
        return True

    return True

# Link all other page that wasn't in game_loop, create the launching page, and menu control
def main():
    running = True
    selected_music_index = 0
    player_name = ""
    mode = "Normal"
    selected_mode = mode

    name_input_active = True
    while name_input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name:
                    name_input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode
                       
        screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 40)
        prompt_text = font.render("Type your name and press 'Enter':", True, (255, 255, 255))
        name_text = font.render(player_name, True, (255, 255, 255))
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    music_file, level_name, _ = musics[selected_music_index]
                    if not game_loop(music_file, player_name, level_name, mode):
                        running = False
                elif event.key == pygame.K_UP:
                    selected_music_index = (selected_music_index - 1) % len(musics)
                elif event.key == pygame.K_DOWN:
                    selected_music_index = (selected_music_index + 1) % len(musics)
                elif event.key == pygame.K_RIGHT:
                    mode = "Rythm" if mode == "Normal" else "Normal"
                    selected_mode = mode
                elif event.key == pygame.K_LEFT:
                    mode = "Rythm" if mode == "Normal" else "Normal"
                    selected_mode = mode
        show_start_menu(selected_music_index, player_name, selected_mode)

main()