import sys, os, pygame
from time import sleep
from sys import stdin, exit
from PodSixNet.Connection import connection, ConnectionListener
from thread import *
from pygame.locals import *

class Client(ConnectionListener):
	'''
	This represents a player: their position and their move/shoot state
	for the skeleton of this class, we referenced PodSixNet examples:
		https://github.com/chr15m/PodSixNet/tree/master/examples
	'''
	def __init__(self, host, port):
		self.Connect((host, port))
		print "client started"
		self.move=[0,0]
		self.shooting=False
		self.running=True
	
	def Loop(self):
		'''
		This is the main loop of the client that: 
		1. Updates the model (pumps server)
		2. Checks for various key presses
		3. Sends keypresses/mouse positions beck to the server
		'''
		connection.Pump()
		self.Pump()
		for event in pygame.event.get():
			if event.type ==KEYDOWN and event.key == K_ESCAPE:
				#disconnect from server
				connection.Close()
				c.running=False
			if event.type == KEYDOWN and event.key == K_a:
				self.move[0]-=1
			if event.type == KEYUP and event.key == K_a:
				self.move[0]+=1
			if event.type == KEYDOWN and event.key == K_d:
				self.move[0]+=1
			if event.type == KEYUP and event.key == K_d:
				self.move[0]-=1
			if event.type == KEYDOWN and event.key == K_w:
				self.move[1]-=1
			if event.type == KEYUP and event.key == K_w:
				self.move[1]+=1
			if event.type == KEYDOWN and event.key == K_s:
				self.move[1]+=1
			if event.type == KEYUP and event.key == K_s:
				self.move[1]-=1
			if event.type == MOUSEBUTTONDOWN:
				self.shooting=True
			if event.type == MOUSEBUTTONUP:
				self.shooting=False

		mousePos=pygame.mouse.get_pos()
		if self.shooting:
			shootDirection=mousePos
		else:
			shootDirection=()
		mb=25 #mouse border (how close to edge we let mouse get)
		ss=view.size
		pygame.mouse.set_pos(self.clamp(mousePos,mb,ss[0]-mb,mb,ss[1]-mb))
		
		connection.Send({'action':'playerState','move':self.move,'shoot':shootDirection})

	def clamp(self,(x,y),xmin,xmax,ymin,ymax):
		'''keeps a coordinate pair within boundaries'''
		return [max(min(xmax, x), xmin),max(min(ymax, y), ymin)]

	def Network_setup(self,data):
		print 'setup complete!'
		view.setup(data)

	def Network_update(self,data):
		view.frame(data['update'])

	def Network_connected(self, data):
		print "You are now connected to the server"
	
	def Network_error(self, data):
		print 'error:', data['error'][1]
		connection.Close()
	
	def Network_disconnected(self, data):
		print 'Server disconnected'

class View(object):
	'''
	The view class is really what the client is doing: visualizing the information passed to it from server
	'''
	def __init__(self):	
		pygame.init()
		self.living=True
		self.size=(0,0)	
		self.font = pygame.font.Font(None, 24)
		self.BLACK    = (   0,   0,   0)
		self.WHITE    = ( 255, 255, 255)
		self.GREEN    = (  25, 255,   25)
		self.DARKGREEN= (   0, 255,    0)
		self.RED      = ( 255,   0,   0)
		self.GREY	  = (200, 200, 200)
		self.size=(900,700)
		os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50,50)
		self.screen   = pygame.display.set_mode(self.size)
		pygame.display.set_caption("KILL KILL Evolution")
		self.background = pygame.Surface(self.screen.get_size())
		self.background = self.background.convert()
		self.background.fill((250, 250, 250))
		self.screen.blit(self.background, (0, 0))

	def startscreen(self):
		'''
		To keep the game from playing right after running command line, a start screen
		is used to prompt the player for a keypress before starting the game.
		'''
		self.background.fill((250, 250, 250))
		self.screen.blit(self.background, (0, 0))
		entermessage= self.font.render('Press enter!', 1, (10, 10, 10))
		self.screen.blit(entermessage, (self.size[0]/2, self.size[1]/2))
		pygame.display.flip()
		notpressed=True
		while notpressed:
			for event in pygame.event.get():
				if event.type ==KEYDOWN and event.key == K_RETURN:
					notpressed=False
				if event.type == pygame.QUIT:
					view.living=False
					notpressed=False

	def setup(self,data):
		'''get some key variables from server model'''
		self.playerSize= data['playerSize']
		self.zombieSize= data['zombieSize']
		self.bulletSize= data['bulletSize']

	def frame(self,data):
		'''
		Update all objects in game based upon data from server
		'''
		self.screen.fill(self.WHITE) #clears everything

		'''draw players'''
		for player in data['players']:
			pygame.draw.rect(self.screen, self.RED,[
				player[0]-self.playerSize/2, 
				player[1]-self.playerSize/2, 
				self.playerSize,self.playerSize])

		'''draw zombies'''	
		for zombie in data['zombies']:
			s=self.zombieSize
			h=s-(zombie[2]*2)
			if h<0:
				h=0
			pygame.draw.rect(self.screen, self.GREEN,[zombie[0]-s/2, zombie[1]-s/2, s,s])
			pygame.draw.rect(self.screen, self.BLACK,[zombie[0]-h/2, zombie[1]-h/2, h,h])
			if not zombie[4]:
				pygame.draw.circle(self.screen, self.GREY,[int(zombie[0]),int(zombie[1])],int(zombie[3]),1)
			else:
				pygame.draw.circle(self.screen, self.RED,[int(zombie[0]),int(zombie[1])],int(zombie[3]),1)

		'''draw bullets'''
		for bullet in data['bullets']:
			pygame.draw.rect(self.screen, self.BLACK,[
				bullet[0]-self.bulletSize/2,
				bullet[1]-self.bulletSize/2,
				self.bulletSize,self.bulletSize])
		for (i,player) in enumerate(data['players']):
			health = self.font.render(str(data['health'][i]), 1, (10, 10, 10))
			self.screen.blit(health, (player[0]-self.playerSize/4, player[1]-self.playerSize/2))

		'''print score'''
		score = self.font.render(str(data['score']),1,(10,10,10))
		self.screen.blit(score,(view.size[0]/2,50))

		pygame.display.flip()

if len(sys.argv) != 2:
	print "Usage:", sys.argv[0], "host:port"
	print "e.g.", sys.argv[0], "localhost:31425"
else:
	host, port = sys.argv[1].split(":")
	view=View()
	while view.living:
		view.startscreen()
		c = Client(host, int(port))
		while c.running and view.living:
			c.Loop()
			sleep(0.0001)
