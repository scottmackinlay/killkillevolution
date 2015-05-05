import sys, random,math,copy,time
from time import sleep, localtime
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from weakref import WeakKeyDictionary

screenSize=(900,700)
zombieSize=16
playerSize=16
bulletSize=4

class ClientChannel(Channel):
	"""
	This is the server representation of a single connected client.
	The syntax for this PodSixNet object can be found:
		https://github.com/chr15m/PodSixNet
	"""
	def __init__(self, *args, **kwargs):
		self.pos=[screenSize[0]/2,screenSize[1]/2]
		self.move=[0,0]
		self.maxhealth=10
		self.health=5
		self.shootDirection=()
		self.bulletTimer=time.time()
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		'''deletes this player if needed'''
		self._server.DelPlayer(self)

	def Network_playerState(self,data):
		'''here is where we listen to the client for specific data'''
		self.move=data['move']
		self.shootDirection=data['shoot']

class Serve(Server):
	'''
	The server class handles all the PodSixNet functions that communicate with the client.
	It inherits from Server, a PodSixNet object
	for the skeleton of this class, we referenced their examples:
		https://github.com/chr15m/PodSixNet/tree/master/examples
	'''
	channelClass = ClientChannel

	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs) 
		print 'Server launched'
	
	def Connected(self, channel, addr):
		channel.Send({'action':'setup',
			'screenSize':screenSize,
			'playerSize':playerSize,
			'zombieSize':zombieSize,
			'bulletSize':bulletSize})
		model.AddPlayer(channel)

	def DelPlayer(self, player):
		model.DelPlayer(player)

	def SendToAll(self, data):
		[p.Send(data) for p in model.players]

	def Update(self):
		if model.players: #only update if there are people in game (else: problems)
			model.Update()
		self.SendToAll({'action':'update',
			'update':model.sendDict})
	
	def Launch(self):
		'''Here is the loop for the server'''
		while True:
			self.Pump()
			self.Update()
			sleep(.01)

class Standard(object):
	'''
	This is a representation of a "standard" zombie. It is the template from which all new 
	zombies deviate from when created. When a zombie successfully hits a player, thist standard
	is altered to better match the zombie that hit the player.
	'''
	def __init__(self):
		self.walk=1
		self.run=1
		self.health=5
		self.prock=100
	def show(self):
		'''useful debugging tool to see what the standard zombie looks like'''
		print self.walk, self.run, self.health, self.prock 

class Zombie(object):
	'''
	The zombie class has attributes for position/velocity, health, walk/run speeds, and proc distance
	It also has methods for updating and evolving/enhancing
	'''
	def __init__(self,standard):
		#positioning randomly around border of game
		if random.randint(0,1):
			if random.randint(0,1):
				self.pos=[random.randint(10,int(screenSize[0]-10)-zombieSize),10]
			else:
				self.pos=[random.randint(10,int(screenSize[0]-10)-zombieSize),screenSize[1]-10]
		else:
			if random.randint(0,1):
				self.pos=[10,random.randint(10,int(screenSize[1]-10)-zombieSize)]
			else:
				self.pos=[screenSize[0]-10,random.randint(10,int(screenSize[1]-10)-zombieSize)]
		#traits of the zombie:
		self.procked=False
		self.living=True
		x=random.randint(-3,3)/3.0
		self.move=[x,math.sqrt(1-x**2)]

		#dev stands for deviation and represents how much this zombie deviates from regZomb
		self.walkDev=random.randint(80,120)/100.0
		self.runDev=random.randint(80,120)/100.0
		self.healthDev=random.randint(80,120)/100.0
		self.prockDistanceDev= random.randint(80,120)/100.0

		self.walk=standard.walk*self.walkDev
		self.run=standard.run*self.runDev
		self.health=standard.health*self.healthDev
		self.maxhealth=copy.copy(self.health)
		self.prockDistance=standard.prock*self.prockDistanceDev

	def dist(self,player): 
		'''returns distances between zombie and player'''
		return math.sqrt((self.pos[0]-player[0])**2+(self.pos[1]-player[1])**2)
		
	def evolve(self):
		'''This is called when the zombie successfully hits a player. By calling this method, the
		template for the zombies (regZomb) is altered to match the traits of the effective zombie'''
		model.regZomb.walk*=self.walkDev
		model.regZomb.run*=self.runDev
		model.regZomb.health*=self.healthDev
		model.regZomb.prock*=self.prockDistanceDev

	def enhance(self):
		'''This method makes everything about the template zombie better. Essentially making the game a little harder'''
		model.regZomb.walk+=.1
		model.regZomb.run+=.1
		model.regZomb.health+=1
		model.regZomb.prock+=10

	def update(self,playerPositions):
		'''
		This is the update function for each zombie. It first determines if any players are close enough to 
		prock (start chasing). Then it moves. Then it checks for collisions
		'''

		'''Checking for nearby players'''
		closestDist=10000 #initialize this value as really far (assume that there is a player closer than this)
		for player in model.players:
			currentDist=self.dist(player.pos)
			if currentDist<closestDist:
				closestPlayer=player
				closestDist=currentDist
		if 0<closestDist<self.prockDistance: 
			self.procked=True
		if not self.procked:
			if not 0<self.pos[0]<screenSize[0]:
				self.move[0]*=-1
			if not 0<self.pos[1]<screenSize[1]:
				self.move[1]*=-1
			self.speed=self.walk
		else:
			self.speed=self.run
			#this section makes the zombie follow the player
			self.move[0]=(closestPlayer.pos[0]-self.pos[0])/(closestDist)
			self.move[1]=(closestPlayer.pos[1]-self.pos[1])/(closestDist)

		'''Move the zombie'''
		self.pos[0]+=self.move[0]*self.speed
		self.pos[1]+=self.move[1]*self.speed

		'''Collision detection for players'''
		#d represents the distance between centerpoints of the zombie and the player	
		d=(zombieSize+playerSize)/2
		if closestPlayer.pos[0]-d<self.pos[0]<closestPlayer.pos[0]+d and closestPlayer.pos[1]-d<self.pos[1]<closestPlayer.pos[1]+d:
			self.living=False
			closestPlayer.health-=2
			self.evolve()
			if all([player.health<=player.maxhealth/2 for player in model.players]) and model.popCap>10: 
			# if all the players are below half health and there are more than ten zombies, make it easier
				model.popCap-=1
			#if a player dies, restart the game:
			if closestPlayer.health<0:
				model.score=0
				model.zombieList=[]
				model.regZomb=Standard()
				for players in model.players:
					players.health=5

		'''collision detection for bullets'''
		#h is the distance between centerpoints of the bullets and the zombies
		h=(zombieSize+bulletSize)/2
		for bullet in model.bulletList:
			#if hit:
			if self.pos[0]-h<bullet.pos[0]<self.pos[0]+h and self.pos[1]-h<bullet.pos[1]<self.pos[1]+h:
				self.procked=True
				bullet.living=False
				self.health-=1
				# if dead:
				if self.health<=0:
					model.score+=1
					if not model.score%20:
						self.enhance()
					self.living=False
					for player in model.players:
						if not random.randint(0,2):
							player.health+=1
					if all([player.health>=player.maxhealth for player in model.players]) and model.popCap<30:
						model.popCap+=1

class Bullet(object):
	'''
	Bullet class where bullets have a start position (the player posiition) and then move linearily towards where the mouse was
	when the bullet was fired
	'''
	def __init__(self,target,position):
		'''figure out where the bullet starts and in what direction it should go'''
		self.speed=5
		self.living=True
		self.pos=position
		dist=math.sqrt((self.pos[0]-target[0])**2+(self.pos[1]-target[1])**2)
		self.direction=[(target[0]-self.pos[0])/dist,
						(target[1]-self.pos[1])/dist]
	def update(self):
		'''move bullet and delete it once it crosses outside of the game window'''
		self.pos[0]+=self.direction[0]*self.speed
		self.pos[1]+=self.direction[1]*self.speed
		if not 0<self.pos[0]<screenSize[0] or not 0<self.pos[1]<screenSize[1]:
			self.living=False

class Model(object):
	'''
	The model class holds the positions and velocities of all ingame objects
	'''
	def __init__(self):
		self.score=0
		self.players=WeakKeyDictionary()
		self.zombieList=[]
		self.popCap=10
		self.bulletList=[]
		self.sendDict={}
		self.regZomb=Standard()
		self.attackspeed=.1 #something between 1 and .1
		
	def AddPlayer(self,channel):
		self.players[channel] = True
		print 'person added!'

	def DelPlayer(self,player):
		del self.players[player]
		print 'person deleted!'

	def Update(self):
		'''Update players'''
		self.playerPositions=[]
		for player in self.players:
			player.pos[0]+=1.25*player.move[0]
			player.pos[1]+=1.25*player.move[1]
			player.pos=self.clamp(player.pos,0,screenSize[0],0,screenSize[1])
			self.playerPositions+=[[player.pos[0],player.pos[1]]]
			if player.shootDirection and time.time()-player.bulletTimer>self.attackspeed:
				player.bulletTimer=time.time()
				self.bulletList+=[Bullet(player.shootDirection,
					copy.copy(player.pos))]

		'''Update zombies'''
		self.zombieList=[zombie for zombie in self.zombieList if zombie.living==True]
		for zombie in self.zombieList:
			zombie.update([player.pos for player in self.players])
		while len(self.zombieList)<self.popCap:
			self.AddZombies()

		'''Update bullets'''
		self.bulletList=[bullet for bullet in self.bulletList if bullet.living==True]
		for bullet in self.bulletList:
			if bullet.living==True:
				bullet.update()

		'''dictionary to send to the clients: locations of all ingame objects'''
		self.sendDict={'players':self.playerPositions,
			'zombies':self.ZombListifier(self.zombieList),
			'bullets':self.Listifier(self.bulletList),
			'health':[player.health for player in model.players],
			'score':model.score}

	def clamp(self,(x,y),xmin,xmax,ymin,ymax):
		'''
		Useful function for coordinates in bounds (keeping player from escaping window)
		'''
		return [max(min(xmax, x), xmin),max(min(ymax, y), ymin)]

	def AddZombies(self):
		self.zombieList+=[Zombie(self.regZomb)]

	def ZombListifier(self,listy):
		'''
		Creates a sendable list of the important zombie attributes. 
		This means that not all the zombie information has to be sent, saving bandwidth for more important stuff
		'''
		return [[item.pos[0],item.pos[1],item.health,item.prockDistance, item.procked] for item in listy if item.living==True]
	def Listifier(self,listy):
		'''
		This creates a list of the positions for any list of items that have a position attribute.
		'''
		return [[item.pos[0],item.pos[1]] for item in listy if item.living==True]
# get command line argument of server:port
if len(sys.argv) != 2:
	print "Usage:", sys.argv[0], "host:port"
	print "e.g.", sys.argv[0], "localhost:31425"
else:
	host, port = sys.argv[1].split(":")
	s = Serve(localaddr=(host, int(port)))
	model=Model()
	s.Launch()
