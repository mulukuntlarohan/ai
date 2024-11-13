import pygame

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        # Set font as None initially; initialize it in draw if it isn’t already
        self.font = None  

    def draw(self, screen):
        if not self.font:  # Lazy initialization of font
            self.font = pygame.font.Font('assets/fonts/game_font.ttf', 24)
        pygame.draw.rect(screen, (0, 128, 255), self.rect)
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(
            text_surface,
            (self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
             self.rect.y + (self.rect.height - text_surface.get_height()) // 2)
        )

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
