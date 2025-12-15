import pygame
import sys

pygame.init()

WIDTH,LENGTH = 900,600
WINDOW = pygame.display.set_mode((WIDTH,LENGTH))
pygame.display.set_caption("haunted house")

clock = pygame.time.Clock ()
FPS = 60

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        WINDOW.fill ((30,30,30))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit
main()