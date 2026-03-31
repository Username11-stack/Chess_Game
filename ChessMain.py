
import pygame as p
import ChessEngine as ce

WIDTH = 800
HEIGHT = 800
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15

# pygame setup
p.init()
screen = p.display.set_mode((WIDTH, HEIGHT))
clock = p.time.Clock()
running = True
gs = ce.gameState()
IMAGES = {}
moveSet = []


def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(f"Chess/Images/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def makeSquares():
    for r in range(0, WIDTH, 10):
        for c in range(0, HEIGHT, 100):
            val = (((r+c)//100 ) % 2)
            if val == 0:
                color = p.Color('White')
            else:
                color = p.Color('Gray')
            p.draw.rect(screen, color, p.Rect(r, c, 100, 100))
        
def drawPieces():
    for r in range(0, WIDTH//100):
        for c in range(0, HEIGHT//100):
            if gs.board[r][c] != '--':
                piece = gs.board[r][c]
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            

while running:
    screen.fill("White")
    makeSquares()
    load_images()
    drawPieces()
    for event in p.event.get():
        if event.type == p.QUIT:
            running = False
        elif event.type == p.MOUSEBUTTONDOWN:
            location = p.mouse.get_pos()
            col = location[0] // SQ_SIZE
            row = location[1] // SQ_SIZE
            sqSelected = (row, col)
            #print(sqSelected)
            moveSet.append(sqSelected)
            #print(moveSet)
            #print(len(moveSet))
            if len(moveSet) == 2:
                if sqSelected != moveSet[0]:
                    gs.makeMove(moveSet[0], moveSet[1])
                    sqSelected = ()
                    moveSet = []
                else:
                    sqSelected = ()
                    moveset = []
            elif len(moveSet) > 2:
                sqSelected = ()
                moveset = []
        elif gs.whiteWon == True or gs.blackWon == True or gs.staleMate == True:
            
            my_font = p.font.SysFont('Comic Sans MS', 30)
            text_surface = my_font.render('THE GAME HAS ENDED', False, (0, 0, 0))
            screen.blit(text_surface, (225,400))

            running = False


    
    p.display.flip()

    clock.tick(80)


p.quit()

