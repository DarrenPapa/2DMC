# Author: Darren Chase Papa
# Version: 0.1
# Build: b
# This build can accept new textures in a directory this will help add and remove textures easier and more organized

import pygame
import sys
import os
import traceback
import tkinter as tk
import pickle
from tkinter import messagebox
import datetime

os.makedirs('./worlds',exist_ok=True)
os.chdir(os.path.dirname(sys.argv[0]))

# Initialize Pygame
pygame.init()
pygame.mixer.init()
icon = pygame.image.load('./assets/icon.ico')
pygame.display.set_icon(icon)

def play(soundfile):
	pygame.mixer.Sound(soundfile).play()

def display_text(screen, text, font_size):
	font = pygame.font.Font(None, font_size)
	text_color = (255, 255, 255)  # White color

	text_surface = font.render(text, True, text_color)
	text_x = (screen.get_width() - text_surface.get_width()) // 2
	text_y = (screen.get_height() - text_surface.get_height())

	screen.blit(text_surface, (text_x, text_y))

# Set up display
screen_size = (700, 700)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2DMC - v0.1")
textures = {}
scripts = {}
block_pick = 0
size = 50
data = {}

def Input_GUI(root=None,title=None,prompt=None,geometry=None,button_text=None,default=None):
	out = default
	root = root or tk.Tk()
	def shoot(item):
		nonlocal out
		out = item
		root.destroy()
	root.geometry(geometry or '200x200')
	if title != None:
		root.title(title)
	tk.Label(root,text=prompt or 'Give input').pack()
	input_ = tk.Entry(root)
	input_.pack()
	tk.Button(root,text=button_text or 'Submit',command=lambda: shoot(input_.get())).pack()
	root.mainloop()
	return out

# Load textures
for file in os.listdir('./assets/textures/'):
	if os.path.isfile('./assets/textures/'+file):
		if file.endswith('.png'):
			pic = pygame.image.load(f'./assets/textures/{file}')
			pic = pygame.transform.scale(pic, (size, size))
			textures[os.path.basename(file).split('.')[0]] = pic
	elif os.path.isdir('./assets/textures/'+file):
		for sfile in os.listdir('./assets/textures/'+file):
			if sfile.endswith('.png'):
				pic = pygame.image.load(f'./assets/textures/{file}/{sfile}')
				pic = pygame.transform.scale(pic, (size, size))
				textures[f'{file}:'+os.path.basename(sfile).split('.')[0]] = pic
			else:
				open('textures.txt','a').write(f'Ignored "./assets/textures/{file}/{sfile}" - {datetime.datetime.now()}')
	else:
		open('textures.txt','a').write(f'Ignored "./assets/textures/{file}/{sfile}" - {datetime.datetime.now()}')

for file in os.listdir('./assets/scripts/'):
	if os.path.isfile('./assets/scripts/'+file):
		try:
			scripts[os.path.basename(file).split('.')[0]] = compile(open(f'./assets/scripts/{file}').read(),f'./assets/scripts/{file}','exec')
		except:
			open('log.txt','w').write(traceback.format_exc()+f'\nFrom assets/scripts/{file}\nDate: {datetime.datetime.now()}')
			exit()
	if os.path.isdir('./assets/scripts/'+file):
		for sfile in os.listdir('./assets/scripts/'+file):
			if os.path.isfile('./assets/scripts/'+file+'/'+sfile):
				try:
					scripts[f'{file}:'+os.path.basename(sfile).split('.')[0]] = compile(open(f'./assets/scripts/{file}/{sfile}').read(),f'./assets/scripts/{file}','exec')
				except:
					open('log.txt','w').write(traceback.format_exc()+f'\nFrom assets/scripts/{file}/{sfile}\nDate: {datetime.datetime.now()}')
					exit()

print(scripts,textures)

# Voxel size and grid
voxel_size = size  # Adjusted size for better visualization
rows = screen_size[1] // voxel_size
cols = screen_size[0] // voxel_size
worldname = Input_GUI(title='World',prompt='World Name:',button_text='Enter',default='world')+'.world'
# Create a 2D array to represent the voxel grid
try:
	voxels = pickle.loads(open('worlds/'+worldname,'rb').read())
except FileNotFoundError:
	voxels = [[None for _ in range(cols)] for _ in range(rows)] 

# Main game loop
def main():
	global block_pick, data, voxels
	clock = pygame.time.Clock()
	running = True
	while running:

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			# Handle voxel placement/removal on mouse click
			if event.type == pygame.MOUSEBUTTONDOWN:
				x, y = pygame.mouse.get_pos()
				col = x // voxel_size
				row = y // voxel_size
				left_click, middle_click, right_click = pygame.mouse.get_pressed()

				if 0 <= col < cols and 0 <= row < rows:
					box = voxels[row][col]
					if right_click and box == None: # place
						voxels[row][col] = tuple(textures.keys())[block_pick]
					if right_click and box != None: # use
						try:
							exec(scripts.get(box,''),{'play':play,'pos':(col,row),'data':data,'tui':Input_GUI,'grid':voxels,'os':os,'mb':messagebox})
						except:
							open('log.txt','w').write(traceback.format_exc())
							exit()
					if middle_click and box != None:
						block_pick = tuple([val for val,_ in textures.items()]).index(box)
					if left_click:
						voxels[row][col] = None

			if event.type == pygame.KEYDOWN:
				key = event.key
				if key == pygame.K_LEFT:
					block_pick += 1
				if key == pygame.K_RIGHT:
					block_pick -= 1

		# Clear the screen
		screen.fill((0, 0, 0))

		if block_pick < 0:
			block_pick = len(textures)-1
		if block_pick >= len(textures):
			block_pick = 0


		for row in range(rows):
			for col in range(cols):

				voxel_texture = voxels[row][col]
				if voxel_texture is not None:
					org = voxel_texture
					tex = textures.get(voxel_texture,textures.get('default:err'))
					if org != None and tex != None:
						screen.blit(tex, (col * voxel_size, row * voxel_size))
					if org != None and tex == None: # handle missing textures
						voxels[row][col] = 'default:err'

		display_text(screen,f'Selected Block: '+tuple(textures.keys())[block_pick].split(':')[-1],50)

		pygame.display.flip()
		clock.tick(30)
		open('./worlds/'+worldname,'wb').write(pickle.dumps(voxels))

	pygame.quit()
	sys.exit()

if __name__ == "__main__":
	main()