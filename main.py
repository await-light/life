import curses
import time
import random
import re


'''
GAME:
	wsad	: move
	up,left.: change direction
	q		: remove block
	e 		: put block
	r 		: open the bag
	Tab		: start text
TEXT:
	up,down	: look at history
	::::::::: Enter content and click on return can send message
BAG:
	up,down	: look for thing
	enter 	: choose

'''

'''
INFACT:80(Don't worry,it won't disturb you)
.-------------------------------.
|								|\n
|								|\n
|								|\n
|								|\n
|		   	  Y(0,0)			|\n GAMESCREEN_Y:23
|		   -gamescreen-			|\n
|								|\n
|								|\n
|								|\n
`-------------------------------`\n
		 GAMESCREEN_X:79
'''

GAMESCREEN_X,GAMESCREEN_Y = 79,23
is_running = True

class BaseCharacter:
	'''
	All the character should dpend on this class
	The position isn't so clear
	Maybe we use it to find other character beside it
	It means if we remove the position,it will continue
	-to run but we won't find any other chacacter!
	'''
	def __init__(self,char,name,attr):
		self.char = char
		self.name = name
		self.attr = attr

class BuiltBlock(BaseCharacter):
	def __init__(self,char,name,ifthrough,posx=None,posy=None,attr=None):
		BaseCharacter.__init__(self,char,name,attr)
		self.ifthrough = ifthrough
		self.posx = posx
		self.posy = posy

class UseThing(BaseCharacter):
	def __init__(self,char,name,attr=None):
		BaseCharacter.__init__(self,char,name,attr)

class Word(BaseCharacter):
	def __init__(self,char,name=None,attr=None):
		BaseCharacter.__init__(self,
			char=char,
			name=name,
			attr=attr)

class Null(UseThing):
	def __init__(self):
		UseThing.__init__(self,
			char=" ",
			name="Null")

class WoodWall(BuiltBlock):
	def __init__(self,posx=None,posy=None):
		BuiltBlock.__init__(self,
			char="#",
			name="WoodWall",
			ifthrough=False,
			posx=posx,
			posy=posy)

class StoneWall(BuiltBlock):
	def __init__(self,posx=None,posy=None):
		BuiltBlock.__init__(self,
			char="#",
			name="StoneWall",
			ifthrough=False,
			posx=posx,
			posy=posy)

class WoodDoor(BuiltBlock):
	def __init__(self,posx=None,posy=None):
		BuiltBlock.__init__(self,
			char="-",
			name="WoodDoor",
			ifthrough=True,
			posx=posx,
			posy=posy,
			attr=curses.A_DIM,
			)

class Player(BaseCharacter):
	def __init__(self,posx,posy,name):
		BaseCharacter.__init__(self,char="Y",name=name,attr=None)
		self.posx = posx
		self.posy = posy
		self.direction = ""
		self.on = None
		self.point = None
		self.bag = [Null,StoneWall,WoodDoor]
		self.hand = self.bag[0]

class Screen:
	'''
	This control the screen,
	And put the update content to the screen.
	'''
	def __init__(self):
		self.stdscr = curses.initscr()
		curses.start_color()
		curses.noecho()
		curses.cbreak()
		self.stdscr.keypad(True)
		self.stdscr.nodelay(False)
		curses.curs_set(0)

	def show(self,update_c):
		# Basic: clear -> update -> refresh -> getkey -> handle key

		# clear
		self.stdscr.clear()
		'''
		Tip: the result of the game.update() is a list.
		It looks like:
		[
			[" ",<Wall obj>," "],
			[" ",<Grass obj>,<Wall obj>],
			[" "," "," "],
			[<Grass obj>,<Player obj>],
			["l","o","g"]
		]
		<class 'str'> - "l","o","g"," "
		<super-BaseCh...> - <Grass obj>,<Player obj>
		'''

		# update
		update_c = update_c
		for index,y in enumerate(update_c):
			for x in y:
				if str(type(x)) == "<class 'str'>":
					self.stdscr.addstr(x)
				elif x.attr != None:
					self.stdscr.addch(x.char,x.attr)
				else:
					self.stdscr.addch(x.char)
			if index != len(update_c)-1:
				self.stdscr.addch("\n")

		# refresh
		self.stdscr.refresh()

		# getkey & handle key
		return self.stdscr.getch()

class Game:
	def __init__(self,screen):
		self.screen = screen
	
		self.blocks = [] # all blocks
		self._mode = "game" # game,text
		self._randomhouse = []
		self._promptlist = []
		self._enterlist = []

		self.player = Player(0,0,"light")
		self.buildhouse(WoodWall,(-1,-1),(-18,-15))
		self.buildhouse(StoneWall,(10,4),(20,-14))

	# run : update & show it on the screen
	def run_forever(self):
		while is_running:
			key = self.screen.show(self.update())
			self.keyhandle(key)

		# Return the original statu
		curses.nocbreak()
		self.screen.stdscr.keypad(False)
		curses.echo()
		curses.endwin()

	# handle the key user typed,no result
	def keyhandle(self,ordkey:int):
		# exit
		if ordkey == 27:
			global is_running
			is_running = False

		# mode:game
		if self._mode == "game":
			movex,movey = 0,0
			if ordkey == ord("w"): # UP
				movey = 1
				self.player.direction = "up"
			elif ordkey == ord("s"): # DOWN
				movey = -1
				self.player.direction = "down"
			elif ordkey == ord("a"): # LEFT
				movex = -1
				self.player.direction = "left"
			elif ordkey == ord("d"): # RIGHT
				movex = 1
				self.player.direction = "right"
			if movex != 0 or movey != 0:
				for wall in [block for block in self.blocks if not block.ifthrough]:
					if (wall.posx == self.player.posx + movex) and \
						(wall.posy == self.player.posy + movey):
						self.prompt("* Touch the wall!")
						break
				else:
					self.player.posx += movex
					self.player.posy += movey

				self.player.point = None
				self.player.on = None
				for block in self.blocks:
					if (block.posx == self.player.posx + movex) and \
						(block.posy == self.player.posy + movey):
						self.player.point = block
					elif (block.posx == self.player.posx) and \
						(block.posy == self.player.posy):
						self.player.on = block

			if ordkey == 259: # UP
				self.player.direction = "up"

			elif ordkey == 258: # DOWN
				self.player.direction = "down"

			elif ordkey == 260: # LEFT
				self.player.direction = "left"
			
			elif ordkey == 261: # RIGHT
				self.player.direction = "right"	
			
			elif ordkey == 9: # Tab
				self._mode = "text"
				self._textindex = 0

			elif ordkey == ord("r"):
				self._mode = "bag"
				self._bagindex = 0
				self._bagpoint = 0

			elif ordkey == ord("e") or ordkey == ord("q"):
				thing = self.player.hand

				if self.player.direction == "up":
					thingpos = (self.player.posx,self.player.posy+1)
				elif self.player.direction == "down":
					thingpos = (self.player.posx,self.player.posy-1)
				elif self.player.direction == "left":
					thingpos = (self.player.posx-1,self.player.posy)
				elif self.player.direction == "right":
					thingpos = (self.player.posx+1,self.player.posy)
				else:
					thingpos = None
					self.prompt("* How to know where to put thing")

				if ordkey == ord("e"):
					if (thingpos != None) and \
						(issubclass(thing,BuiltBlock)) and \
						(thingpos not in [(block.posx,block.posy) for block in self.blocks]):
						self.blocks.append(thing(*thingpos))
					else:
						self.prompt(f"* Put failed")

				elif ordkey == ord("q"):
					for block in self.blocks:
						if (block.posx,block.posy) == thingpos:
							self.blocks.remove(block)
							break
					else:
						self.prompt(f"* Remove failed")


		# mode:text
		elif self._mode == "text":
			if ordkey == 9: # Tab
				self._mode = "game"
				self._enterlist = [] 

			elif ordkey == 259: # UP
				if len(self._promptlist[::-1][self._textindex:]) > 10:
					self._textindex += 1 

			elif ordkey == 258: # DOWN
				if self._textindex > 0:
					self._textindex -= 1

			elif ordkey == 263: # backspace
				if len(self._enterlist) >= 1:
					del self._enterlist[-1]

			elif ordkey == 10: # enter
				if self._enterlist != []:
					text = "".join(self._enterlist).strip()
					if text != "":
						self.handletext(text)
					self._enterlist = []

			elif ordkey >= 32 and ordkey <= 126 and len(self._enterlist) < 79:
				self._enterlist.append(chr(ordkey))

		elif self._mode == "bag":
			if ordkey == ord("r"):
				self._mode = "game"

			elif ordkey == 259: # UP
				if self._bagindex > 0:
					self._bagindex -= 1
				if self._bagpoint > 0:
					self._bagpoint -= 1
				
			elif ordkey == 258: # DOWN
				if len(self.player.bag[self._bagindex:]) > 6:
					self._bagindex += 1 
				if self._bagpoint < len(self.player.bag)-1:
					self._bagpoint += 1

			elif ordkey == 10:
				self.player.hand = self.player.bag[self._bagpoint]
				self._mode = "game"


	# update the content,return the content
	def update(self):
		up = self.player.posy + 11
		down = self.player.posy - 12
		right = self.player.posx + 38 
		left = self.player.posx - 39

		gamescreen = [[" " for i in range(GAMESCREEN_X)] for line in range(GAMESCREEN_Y+1)]
		tosidex,tosidey = int((GAMESCREEN_X-1)/2),int((GAMESCREEN_Y-1)/2)
		# -38~38 range(left,right+1)
		# -12~11 range(down,up+1)
		for block in self.blocks:
			if block.posx in range(left,right+1) and block.posy in range(down,up+1):
				gamescreen[tosidey+(self.player.posy-block.posy)][tosidex+(block.posx-self.player.posx)] = block

		gamescreen[tosidey][tosidex] = self.player

		# prompt
		if self._mode != "text":
			num = 3
			for index,text in enumerate(self._promptlist[::-1]):
				if index < num:
					gamescreen[-(index+1)][:len(text)] = [Word(c) for c in text]
		else:
			num = 10
			for index,text in enumerate(self._promptlist[::-1][self._textindex:]):
				if index < num:
					gamescreen[-(index+1)-1][:len(text)] = [Word(c) for c in text]
			gamescreen[-1][:len(self._enterlist)] = [Word(c) for c in self._enterlist]

		# statu
		_statu = []
		if self._mode != "bag":
			'''
				Mode:game/text
				Pos:15,5
				Direction:right
				On:
				Point:
			'''
			_statu.append(f"Mode:{self._mode}")
			_statu.append(f"Pos:{self.player.posx},{self.player.posy}")
			_statu.append(f"Direction:{self.player.direction}")
			if self.player.on != None:
				on = self.player.on.name 
			else:
				on = ""
			_statu.append(f"On:{on}")
			if self.player.point != None:
				point = self.player.point.name 
			else:
				point = ""
			_statu.append(f"Point:{point}")
			if self.player.hand != None:
				hand = self.player.hand.__name__
			else:
				hand = ""
			_statu.append(f"Hand:{hand}")
		else:
			'''
				Mode:bag
				a
				b
				c
				d
				e
				f
			'''
			_statu.append(f"Mode:{self._mode}")
			_statu.append(f"'Key_UP' or 'Key_DOWN'.'Enter' to choose.")
			_statu.append(f" ")
			for index,thing in enumerate(self.player.bag[self._bagindex:]):
				if index < 6:
					if index+self._bagindex == self._bagpoint:
						_statu.append(f"<{index+self._bagindex}> {thing.__name__}")
					else:
						_statu.append(f"{index+self._bagindex} {thing.__name__}")

		for index,element in enumerate(_statu):
			gamescreen[index][:len(element)] = [Word(c) for c in element]

		return gamescreen

	# prompt,it can appear everywhere
	def prompt(self,text:str):
		lasti = 0
		for i in range(0,len(text),20)[1:]:
			self._promptlist.append(text[lasti:i])
			lasti = i
		self._promptlist.append(text[lasti:])

	# a function to build house
	def buildhouse(self,
		wallmaterial,
		originpeer:tuple,
		targetpeer:tuple):
		ax,ay = originpeer[0],originpeer[1]
		bx,by = targetpeer[0],targetpeer[1]

		allpeer = []

		for x in range(min(ax,bx)+1,max(ax,bx)):
			allpeer.append((x,max(ay,by)))
			allpeer.append((x,min(ay,by)))

		for y in range(min(ay,by)+1,max(ay,by)):
			allpeer.append((max(ax,bx),y))
			allpeer.append((min(ax,bx),y))

		doorpos = random.choice(allpeer)
		allpeer.remove(doorpos)

		# bulid walls
		for peerx,peery in allpeer:
			self.blocks.append(wallmaterial(posx=peerx,posy=peery))

		# build door
		self.blocks.append(WoodDoor(doorpos[0],doorpos[1]))

	# handle text user types
	def handletext(self,text):
		text = f"* {self.player.name}:{text}"
		self.prompt(text)

if __name__ == '__main__':
	screen = Screen()
	game = Game(screen)
	game.run_forever()