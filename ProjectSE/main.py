import pygame
import pygame_gui.elements.ui_button as ui_button
from pygame_gui.core import ObjectID
import sys
import math
import pygame_gui
import random
import time
import json
import sqlite3

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS game_results
                 (username TEXT, mode TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

# Function to save game result
def save_game_result(user_name, difficulty, final_score):
    try:
        conn = sqlite3.connect('game_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO game_results (USERNAME, MODE, SCORE) VALUES (?, ?, ?)',
                  (user_name, difficulty, final_score))
        conn.commit()
        print("Data inserted successfully")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


try:
    # Read JSON file
    with open('quick_start.JSON') as f:
        data = json.load(f)

    # Example usage
    print("JSON data loaded successfully:", data)

except FileNotFoundError:
    print("Error: JSON file not found.")
except json.JSONDecodeError:
    print("Error: Invalid JSON format.")
except Exception as e:
    print("Error:", e)


# Initialize pygame
pygame.init()

# Define screen properties
SCREENWIDTH, SCREENHEIGHT = 1200, 800
FPS = 60
pygame.display.set_caption("Math Mastery Flip")

# Initialize display surface
screen = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))

# Load background image
bg = pygame.image.load('BG3.png').convert()
bg_width = bg.get_width()
tiles = math.ceil(SCREENWIDTH / bg_width) + 1
scroll = 0

# Define colors
white = (255, 255, 255)
green = (26, 46, 0)
green2 = (30, 66, 37)
black = (0, 0, 0)
light_green = (110, 255, 105)

# Title and Text
title_font = pygame.font.Font('FontGame.ttf', 72)
btn_font = pygame.font.Font('FontGame.ttf', 30)
text_font = pygame.font.Font('Gamer.ttf', 60)
number_font = pygame.font.Font(None, 36)  # Added font for numbers

# Variables
user_name = ''
difficulty = ''
rows = 3
cols = 4
selected_numbers = []
delay_counter = 0  # Added delay counter
round_time_limit = 30  # Time limit for each round in seconds
final_score = ''

# SFX variables
btn_sfx = pygame.mixer.Sound("btnSFX.mp3")
correct_sfx = pygame.mixer.Sound("correct.mp3")  # Load correct sound
wrong_sfx = pygame.mixer.Sound("wrong.mp3")      # Load wrong sound
time_up_sfx = pygame.mixer.Sound("wrong.mp3")  # Load time up sound



def title_text(text, font, text_col, outline_col, x, y):
    text_surf = font.render(text, True, outline_col)
    screen.blit(text_surf, (x - 2, y - 2))
    screen.blit(text_surf, (x + 2, y - 2))
    screen.blit(text_surf, (x - 2, y + 2))
    screen.blit(text_surf, (x + 2, y + 2))

    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_text(text, font, color, outline_col, x, y):
    text_surface = font.render(text, True, outline_col)
    screen.blit(text_surface, (x - 2, y - 2))
    screen.blit(text_surface, (x + 2, y - 2))
    screen.blit(text_surface, (x - 2, y + 2))
    screen.blit(text_surface, (x + 2, y + 2))

    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_bg():
    top_menu = pygame.draw.rect(screen, green2, [0, 0, SCREENWIDTH, 130], 0)
    bottom_menu = pygame.draw.rect(screen, green2, [0, SCREENHEIGHT - 100, SCREENWIDTH, 130], 0)



class Game:
    def __init__(self):
        self.ui_manager = pygame_gui.UIManager((SCREENWIDTH, SCREENHEIGHT), theme_path="quick_start.JSON")
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.gameStateManager = GameStateManager('start')
        self.start = Start(self.screen, self.gameStateManager, self.ui_manager)
        self.mode = Mode(self.screen, self.gameStateManager, self.ui_manager)
        self.gameScreen = GameScreen(self.screen, self.gameStateManager, self.ui_manager)
        self.gameResult = GameResult(self.screen, self.gameStateManager, self.ui_manager)
        self.state = {'start': self.start, 'mode': self.mode, 'gameScreen': self.gameScreen, 'gameResult': self.gameResult}

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.ui_manager.process_events(event)
                if self.gameStateManager.get_State() == "gameScreen":
                    self.state["gameScreen"].handle_events(event)
            self.ui_manager.update(FPS / 1000)
            self.state[self.gameStateManager.get_State()].run()
            self.ui_manager.draw_ui(screen)
            pygame.display.flip()
            self.clock.tick(FPS)



class GameScreen:
    def __init__(self, display, gameStateManager, ui_manager):
        self.display = display
        self.gameStateManager = gameStateManager
        self.ui_manager = ui_manager

        self.title_font = title_font
        self.text_font = text_font


        self.user_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 20), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#user-label"
        )

        # Create the mode label
        self.mode_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 50), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#mode-label"
        )

        # Create the equation label
        self.equation_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((500, 50), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#equation-label"
        )

        # Generate and store the random numbers once
        self.board_numbers = self.generate_board_numbers()
        self.revealed = [False] * (rows * cols)  # Added attribute to track revealed numbers
        self.reveal_timer = 0  # Timer to track the delay

        # Generate the first equation
        self.current_equation, self.correct_answer = self.generate_equation()

        self.round_timer = None  # Initialize round_timer to None
        self.score = 0  # Initialize score

    def reset(self):
        self.board_numbers = self.generate_board_numbers()
        self.revealed = [False] * (rows * cols)  # Reset the revealed state
        self.current_equation, self.correct_answer = self.generate_equation()
        self.round_timer = None  # Initialize round_timer to None
        self.score = 0  # Initialize score

        self.user_label.show()
        self.mode_label.show()

    def set_round_timer(self, difficulty):
        if difficulty == 'EASY':
            self.round_timer = 120  # 60 seconds for EASY
        elif difficulty == 'MEDIUM':
            self.round_timer = 90  # 45 seconds for MEDIUM
        elif difficulty == 'HARD':
            self.round_timer = 20  # 30 seconds for HARD
        else:
            self.round_timer = 30  # Default to 30 seconds if difficulty is not set

    def generate_board_numbers(self):
        return [random.randint(1, 10) for _ in range(rows * cols)]

    def generate_equation(self):
        operations = ['+', '-', '*', '/']
        operation = random.choice(operations)

        if operation == '+':
            target = random.randint(5, 20)
            valid_pairs = [(a, b) for a in self.board_numbers for b in self.board_numbers if a + b == target]
        elif operation == '-':
            target = random.randint(1, 10)
            valid_pairs = [(a, b) for a in self.board_numbers for b in self.board_numbers if a - b == target]
        elif operation == '*':
            target = random.randint(5, 100)
            valid_pairs = [(a, b) for a in self.board_numbers for b in self.board_numbers if a * b == target]
        else:  # operation == '/'
            target = random.randint(1, 10)
            valid_pairs = [(a, b) for a in self.board_numbers for b in self.board_numbers if b != 0 and a % b == 0 and a / b == target]

        if valid_pairs:
            correct_pair = random.choice(valid_pairs)
            equation_text = f"(_ {operation} _ = {target})"
            return equation_text, correct_pair
        else:
            return self.generate_equation()

    def draw_board(self):
        global rows
        global cols

        for i in range(cols):
            for j in range(rows):
                index = j * cols + i
                piece = pygame.draw.rect(screen, light_green, [i * 150 + 330, j * 150 + 200, 130, 130], 0, 5)

                if self.revealed[index]:
                    random_number = self.board_numbers[index]
                    text_surface = number_font.render(str(random_number), True, black)
                    text_rect = text_surface.get_rect(center=(i * 150 + 395, j * 150 + 265))
                    screen.blit(text_surface, text_rect)

                    # Draw stroke effect for the revealed cards
                    pygame.draw.rect(screen, green2, [i * 150 + 330, j * 150 + 200, 130, 130], 5)

                # Draw stroke effect for the selected cards
                for _, idx in selected_numbers:
                    if idx == index:
                        pygame.draw.rect(screen, green2, [i * 150 + 330, j * 150 + 200, 130, 130], 5)

    def handle_events(self, event):
        global delay_counter  # Added delay_counter to global scope

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for i in range(cols):
                for j in range(rows):
                    rect = pygame.Rect(i * 150 + 330, j * 150 + 200, 130, 130)
                    if rect.collidepoint(pos):
                        selected_number = self.board_numbers[j * cols + i]
                        if len(selected_numbers) < 2 and not self.revealed[j * cols + i]:
                            self.revealed[j * cols + i] = True  # Reveal the number
                            selected_numbers.append((selected_number, j * cols + i))

                        if len(selected_numbers) == 2:
                            delay_counter = 60  # Set delay counter to 60 frames (1 second at 60 FPS)

    def check_answer(self):
        global selected_numbers
        correct = False

        if len(selected_numbers) < 2:
            return

        if "+" in self.current_equation:
            correct = sum(num for num, idx in selected_numbers) == sum(self.correct_answer)
        elif "-" in self.current_equation:
            correct = abs(selected_numbers[0][0] - selected_numbers[1][0]) == abs(self.correct_answer[0] - self.correct_answer[1])
        elif "*" in self.current_equation:
            correct = selected_numbers[0][0] * selected_numbers[1][0] == self.correct_answer[0] * self.correct_answer[1]
        elif "/" in self.current_equation:
            if selected_numbers[1][0] != 0:  # Prevent division by zero
                correct = selected_numbers[0][0] / selected_numbers[1][0] == self.correct_answer[0] / self.correct_answer[1]

        if correct:
            print("Correct!")
            correct_sfx.play()  # Play correct sound
            selected_numbers = []
            self.score += 1  # Update score
            self.board_numbers = self.generate_board_numbers()
            self.revealed = [False] * (rows * cols)  # Reset the revealed state
            self.current_equation, self.correct_answer = self.generate_equation()
            # Do not reset the round timer
        else:
            print("Try again!")
            wrong_sfx.play()  # Play wrong sound
            self.reveal_timer = pygame.time.get_ticks()  # Set the timer for hiding the numbers

    def display_result(self, final_score):
        # Create a green rectangle to display the result
        result_rect = pygame.draw.rect(screen, green2, [200, 200, 800, 400], 0)

        # Print the stored values
        draw_text(f"Username: {user_name}", self.text_font, white, green, 300, 250)
        draw_text(f"Mode: {difficulty}", self.text_font, white, green, 300, 300)
        draw_text(f"Final Score: {final_score}", self.text_font, white, green, 300, 350)

        self.reset()

    def handle_time_up(self):
        print("Time's Up!")
        time_up_sfx.play()  # Play time up sound
        self.board_numbers = self.generate_board_numbers()
        self.revealed = [False] * (rows * cols)  # Reset the revealed state
        self.current_equation, self.correct_answer = self.generate_equation()
        self.round_timer = self.set_round_timer(difficulty)  # Reset the round timer

    def run(self):
        global delay_counter  # Access delay_counter in run method
        global selected_numbers

        if self.round_timer is None:  # Only set the timer once when the game starts
            self.set_round_timer(difficulty)

        # bgloop
        global scroll
        for i in range(0, tiles):
            self.display.blit(bg, (i * bg_width + scroll, 0))
        scroll -= 1

        if abs(scroll) > bg_width:
            scroll = 0

        self.user_label.set_text(f"USER: {user_name}")
        self.mode_label.set_text(f"MODE: {difficulty}")

        draw_bg()
        self.draw_board()
        draw_text(f"EQUATION: {self.current_equation}", self.text_font, white, green, 430, 35)

        # Hide the numbers after a short delay if the pair is incorrect
        if self.reveal_timer and pygame.time.get_ticks() - self.reveal_timer > 1000:
            for _, idx in selected_numbers:
                self.revealed[idx] = False  # Hide the numbers again
            selected_numbers = []
            self.reveal_timer = 0  # Reset the timer

        # Check answer after delay_counter reaches 0
        if delay_counter > 0:
            delay_counter -= 1
            if delay_counter == 0:
                self.check_answer()

        # Update and display the round timer
        self.round_timer -= 1 / FPS
        draw_text(f"TIME: {int(self.round_timer)}", self.text_font, white, green, 990, 20)
        if self.round_timer <= 0:
            self.round_timer = 0  # Ensure the timer doesn't go negative
            self.user_label.kill()
            self.mode_label.kill()
            global final_score
            final_score = self.score
            self.gameStateManager.set_State("gameResult")  # Change the game state to gameResult
            return

        # Display the score
        draw_text(f"SCORE: {self.score}", self.text_font, white, green, 990, 60)



        pygame.display.update()


class GameResult:
    def __init__(self, display, gameStateManager, ui_manager):
        self.display = display
        self.gameStateManager = gameStateManager
        self.ui_manager = ui_manager

        self.title_font = title_font

        self.user = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((450, 300), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#user-lbl"
        )

        self.mode = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((450, 340), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#mode-lbl"
        )

        self.score = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((450, 380), (300, 50)),
            manager=self.ui_manager,
            text="",
            object_id="#score-lbl"
        )

        self.exit_btn = ui_button.UIButton(
            relative_rect=pygame.Rect((420, 450), (400, 50)),
            text='Quit Game',
            manager=self.ui_manager,
            object_id=ObjectID(object_id="#exit-button")
        )

        self.exit_btn.visible = False

    def handle_button_events(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.exit_btn:
                        user_name = self.user
                        difficulty = self.mode
                        final_score = self.score
                        save_game_result(user_name, difficulty, final_score)
                        pygame.quit()
                        pygame.quit()


    def run(self):
        if self.gameStateManager.get_State() == "gameResult":
            self.exit_btn.visible = True
            self.handle_button_events()

        self.user.set_text(f"USER: {user_name}")
        self.mode.set_text(f"MODE: {difficulty}")
        self.score.set_text(f"SCORE: {final_score}")

        global scroll
        for i in range(0, tiles):
            self.display.blit(bg, (i * bg_width + scroll, 0))
        scroll -= 1

        if abs(scroll) > bg_width:
            scroll = 0


        title_text("Math Mastery Flip", self.title_font, white, green, 300, 50)

class Mode:
    def __init__(self, display, gameStateManager, ui_manager):
        self.display = display
        self.gameStateManager = gameStateManager
        self.ui_manager = ui_manager

        # Initialize fonts
        self.title_font = title_font

        # Create buttons
        self.easy_btn = ui_button.UIButton(
            relative_rect=pygame.Rect((450, 400), (300, 50)),
            text='EASY',
            manager=self.ui_manager,
            object_id=ObjectID(object_id="#easy-button")
        )
        self.medium_btn = ui_button.UIButton(
            relative_rect=pygame.Rect((450, 450), (300, 50)),
            text='MEDIUM',
            manager=self.ui_manager,
            object_id=ObjectID(object_id="#medium-button")
        )
        self.hard_btn = ui_button.UIButton(
            relative_rect=pygame.Rect((450, 500), (300, 50)),
            text='HARD',
            manager=self.ui_manager,
            object_id=ObjectID(object_id="#hard-button")
        )

        # Make buttons initially invisible
        self.easy_btn.visible = False
        self.medium_btn.visible = False
        self.hard_btn.visible = False


    def handle_button_events(self):
        global difficulty
        global round_time_limit

        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.easy_btn:
                        self.gameStateManager.set_State("gameScreen")
                        difficulty = 'EASY'
                        btn_sfx.play()
                        self.hide_buttons()
                    elif event.ui_element == self.medium_btn:
                        self.gameStateManager.set_State("gameScreen")
                        difficulty = 'MEDIUM'
                        btn_sfx.play()
                        self.hide_buttons()
                    elif event.ui_element == self.hard_btn:
                        self.gameStateManager.set_State("gameScreen")
                        difficulty = 'HARD'

                        btn_sfx.play()
                        self.hide_buttons()

    def hide_buttons(self):
        # Hide all buttons
        self.easy_btn.visible = False
        self.medium_btn.visible = False
        self.hard_btn.visible = False

    def run(self):
        if self.gameStateManager.get_State() == "mode":
            # Show the "EASY" button only when game state is "mode"
            self.easy_btn.visible = True
            self.medium_btn.visible = True
            self.hard_btn.visible = True

            self.handle_button_events()

        # bgloop
        global scroll
        for i in range(0, tiles):
            self.display.blit(bg, (i * bg_width + scroll, 0))
        scroll -= 1

        if abs(scroll) > bg_width:
            scroll = 0

        # Render text with custom font
        title_text("Math Mastery Flip", self.title_font, white, green, 300, 50)

class Start:
    def __init__(self, display, gameStateManager, ui_manager):
        self.display = display
        self.gameStateManager = gameStateManager
        self.ui_manager = ui_manager

        self.title_font = title_font

        # Create UI elements
        self.create_ui_elements()

    def create_ui_elements(self):
        # Create a text box
        self.text_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((450, 350), (300, 50)),
            manager=self.ui_manager
        )

        # Create a button
        self.start_btn = ui_button.UIButton(
            relative_rect=pygame.Rect((450, 430), (300, 50)),
            text='START',
            manager=self.ui_manager,
            object_id=ObjectID(object_id="#start-button")
        )

    def reset(self):
        # Recreate the UI elements
        self.create_ui_elements()

    def run(self):
        global user_name

        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_btn:
                        user_name = self.text_entry.get_text()
                        if user_name == '':
                            self.gameStateManager.set_State("start")
                        else:
                            self.gameStateManager.set_State("mode")
                            self.text_entry.kill()
                            self.start_btn.kill()

        # bgloop
        global scroll
        for i in range(0, tiles):
            self.display.blit(bg, (i * bg_width + scroll, 0))
        scroll -= 1

        if abs(scroll) > bg_width:
            scroll = 0

        # Render text with custom font
        title_text("Math Mastery Flip", self.title_font, white, green, 300, 50)


class GameStateManager:
    def __init__(self, currentState):
        self.currentState = currentState

    def get_State(self):
        return self.currentState

    def set_State(self, state):
        self.currentState = state


if __name__ == '__main__':
    game = Game()
    game.run()