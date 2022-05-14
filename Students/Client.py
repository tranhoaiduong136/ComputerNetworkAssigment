from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	SPEEDING = 4
	NORMAL = 5
	BACKWARD = 6
	FORWARD = 7
	# Behaviours:
	SPEEDUP = False
	BACKWARDING = False

	####Reset
	def resetThisSession(self,lFilename):
		self.lState = [self.READY]*len(lFilename)
		self.lFrameNbr = [0]*len(lFilename)
		self.fileidx = 0

		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1

		self.fileName=lFilename[self.fileidx]
		self.frameLost = 0
		self.statExpRtpNb = 0
		self.statTotalFrames = 0
		self.statFrameRate = 0
		self.statTotalPlayTime = 0
		self.statFractionLost = 0

		self.statLabel4.configure(text = "Filename: "+self.fileName)
		self.label.image = None
		self.updateStatsLabel()

	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, lFilename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpSocket = None
		self.rtpPort = int(rtpport)
		self.connectToServer()
		self.lFileName = lFilename
		self.lImg = [None]*len(lFilename)
		
		self.createWidgets()

		self.resetThisSession(lFilename)
		#SETUP when create client
		# self.setupMovie()
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Modal window properties"""
		self.master.resizable(False, False) 
		
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] = self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create Info button
		self.info = Button(self.master, width=20, padx=3, pady=3)
		self.info["text"] = "Info"
		self.info["command"] =  self.showInfo
		self.info.grid(row=1, column=4, padx=2, pady=2)

		# Create speedUp button
		self.speedUp = Button(self.master, width=20, padx=3, pady=3)
		self.speedUp["text"] = "Speed up"
		self.speedUp["command"] =  self.speedUpMovie
		self.speedUp.grid(row=2, column=4, padx=2, pady=2)

		# Create backward button
		self.backward = Button(self.master, width=20, padx=3, pady=3)
		self.backward["text"] = "Backward"
		self.backward["command"] =  self.backwardMovie
		self.backward.grid(row=3, column=4, padx=2, pady=2)

		# Create switch button
		self.switch = Button(self.master, width=20, padx=3, pady=3)
		self.switch["text"] = "Switch"
		self.switch["command"] =  self.switchMovie
		self.switch["state"] = "disable"
		self.switch.grid(row=3, column=3, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height = 19)
		self.label.grid(row=0, column=0, columnspan=5, sticky=W+E+N+S, padx=5, pady=5) 
	
		#statlable
		self.statLabel1 = Label(self.master, height = 3, width = 20)
		self.statLabel1.grid(row = 2, column = 0,sticky=W+E+N+S, padx=5, pady=5)
		self.statLabel2 = Label(self.master, height = 3, width = 20)
		self.statLabel2.grid(row = 2, column = 1,sticky=W+E+N+S, padx=5, pady=5)
		self.statLabel3 = Label(self.master, height = 3, width = 20)
		self.statLabel3.grid(row = 2, column = 2, columnspan = 2, sticky=W+E+N+S, padx=5, pady=5)
		self.statLabel4 = Label(self.master, height = 3, width = 20)
		self.statLabel4.grid(row = 3, column = 0, columnspan = 3, sticky=W+E+N+S)
		
	def setupMovie(self):
		"""Setup button handler."""
		#TODO
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
			###Switch###
			self.switch["state"] = "normal" if len(self.lFileName) > 1 else "disable"
	
	def exitClient(self):
		"""Teardown button handler."""
		#TODO
		self.sendRtspRequest(self.TEARDOWN)
		try:
			for i in range(len(self.lImg)):
				f=self.lImg[i]
				self.lImg[i]=None
				if f==None: continue
				os.remove(f) # Delete the cache image from video
		except:
			print('already remove image')
		self.switch["state"] = "disable"

	def pauseMovie(self):
		"""Pause button handler."""
		#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		if self.state == self.READY:
			self.statStartTime = time.perf_counter_ns()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			try:
				data = self.rtpSocket.recv(32768) # (20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
					# print("Current Seq Num: " + str(currFrameNbr))
					

					self.curTime = time.perf_counter_ns() #get current time
					if abs(currFrameNbr - self.lFrameNbr[self.fileidx]) != 1:
						self.frameLost += 1
					if currFrameNbr != self.lFrameNbr[self.fileidx]: # Discard the late packet
						self.lFrameNbr[self.fileidx] = currFrameNbr
						self.lImg[self.fileidx] = self.writeFrame(rtpPacket.getPayload())
						self.updateMovie(self.lImg[self.fileidx])


					self.statTotalPlayTime = self.statTotalPlayTime + (self.curTime - self.statStartTime) #cal total play time
					self.statStartTime =  self.curTime

					self.statExpRtpNb = self.statExpRtpNb + 1 #Num of Frame get
					# if currFrameNbr - self.statExpRtpNb != self.frameLost:
					# 	self.frameLost = self.frameLost + 1 #increase number of lost frame if there are more frames lost
					
					#get frame rate

					if self.statTotalPlayTime == 0 :
						self.statFrameRate =  0
					else:
						self.statFrameRate = self.statTotalFrames / (self.statTotalPlayTime / 1000000000.0)
					self.statFractionLost = self.frameLost / (self.statExpRtpNb + self.frameLost)
					self.statTotalFrames = self.statTotalFrames + 1
					self.updateStatsLabel()

			except:
				if self.state==self.INIT and self.rtpSocket:
					try:
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
					except:
						print("RTP already closed")
					self.rtpSocket = None
				if self.state != self.PLAYING: break
					
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		#TODO
		cache = CACHE_FILE_NAME + str(self.sessionId) + self.fileName + CACHE_FILE_EXT
		tmpfile = open(cache, "wb")
		tmpfile.write(data)
		tmpfile.close()
		self.img = cache
		return cache
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		if not imageFile:
			self.label.image = None
			return
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
			threading.Thread(target=self.recvRtspReply).start()
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode == self.SETUP and self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			lfilename = ",".join(self.lFileName)
			request = ("SETUP " + lfilename + " RTSP/1.0\n"
				+ "CSeq: " + str(self.rtspSeq) + "\n"
				+ "Transport: RTP/UDP; client_port= " + str(self.rtpPort)
			)
			# Keep track of the sent request.
			self.requestSent = self.SETUP
		
		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = ("PLAY " + str(self.fileName) + " RTSP/1.0\n"
				+ "Cseq: " + str(self.rtspSeq) + "\n"
				+ "Session: " + str(self.sessionId)
			)
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = ("PAUSE " + str(self.fileName) + " RTSP/1.0\n"
				+ "Cseq: " + str(self.rtspSeq) + "\n"
				+ "Session: " + str(self.sessionId)
			)
			# Keep track of the sent request.
			self.requestSent = self.PAUSE
			
		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = ("TEARDOWN all RTSP/1.0\n"
				+ "Cseq: " + str(self.rtspSeq) + "\n"
				+ "Session: " + str(self.sessionId)
			)
			# Keep track of the sent request.
			self.requestSent = self.TEARDOWN
			self.state = self.INIT

		elif requestCode == self.SPEEDING and not self.state == self.INIT:
			self.rtspSeq = self.rtspSeq + 1
			request = f"SPEEDUP {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"

		elif requestCode == self.NORMAL and not self.state == self.INIT:
			self.rtspSeq = self.rtspSeq + 1
			request = f"NORMAL {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"

		elif requestCode == self.BACKWARD and not self.state == self.INIT:
			self.rtspSeq = self.rtspSeq + 1
			request = f"BACKWARD {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"

		elif requestCode == self.FORWARD and not self.state == self.INIT:
			self.rtspSeq = self.rtspSeq + 1
			request = f"FORWARD {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"

		else:
			return
		self.rtspSocket.send(request.encode())

		print('\nData sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			try:
				reply = self.rtspSocket.recv(2048)
				
				if reply: 
					self.parseRtspReply(reply.decode())
			except:
				break
			
			
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		request = data.split('\n')
		seqNum = int(request[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(request[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(request[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						self.state = self.READY
						
						# Open RTP port.
						self.openRtpPort() 
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						threading.Thread(target=self.listenRtp).start()
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
					elif self.requestSent == self.TEARDOWN:
						self.resetThisSession(self.lFileName)

	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.state=self.READY
			self.rtpSocket.bind((self.serverAddr, self.rtpPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Unable to bind RTP port %d to server' %self.rtpPort)
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		curState = self.state
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
			try:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
			except:
				print("RTSP already closed")
			self.master.destroy()
		else: # When the user presses cancel, resume playing.
			if curState==self.PLAYING: self.playMovie()

	def showInfo(self):
		"""show info"""
		currState = self.state
		self.pauseMovie()
		info = "Filemane: " + self.fileName + "\nRTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nTransport: RTP/UDP\nclient_port= " + str(self.rtpPort) + '\nSession: ' + str(self.sessionId)
		tkinter.messagebox.showinfo("Info",info)
		if currState == self.PLAYING:
			self.playMovie()

	def speedUpMovie(self):
		if self.state == self.PLAYING:
			# self.sendRtspRequest(self.PAUSE)
			if self.SPEEDUP:
				self.speedUp.configure(text = 'Speed up')
				self.sendRtspRequest(self.NORMAL)
				self.SPEEDUP = False
			else:
				self.speedUp.configure(text = 'Normal')
				self.sendRtspRequest(self.SPEEDING)
				self.SPEEDUP = True
			# self.sendRtspRequest(self.PLAY)

	def backwardMovie(self):
		if self.BACKWARDING:
			self.backward.configure(text = 'Backward')
			self.sendRtspRequest(self.FORWARD)
			self.BACKWARDING = False
		else:
			self.backward.configure(text = 'Forward')
			self.sendRtspRequest(self.BACKWARD)
			self.BACKWARDING = True
	
	def switchMovie(self):
		self.lState[self.fileidx]=self.state
		self.pauseMovie()
		while self.state!=self.READY:
			continue
		self.fileidx+=1
		self.fileidx%=len(self.lFileName)
		self.fileName=self.lFileName[self.fileidx]
		self.statLabel4.configure(text = "Filename: "+self.fileName)
		self.updateMovie(self.lImg[self.fileidx])
		if self.lState[self.fileidx]!=self.PLAYING: return
		while True:
			if self.state!=self.READY: continue
			self.playMovie()
			break
			
	def updateStatsLabel(self):
		self.statLabel1.configure(text = 'Total Frames Received: ' + str(self.statTotalFrames))
		self.statLabel2.configure(text = "Packet Lost Rate: " + str("{:0.3f}".format(self.statFractionLost)))
		self.statLabel3.configure(text = "Frame Rate: " + str("{:0.3f}".format(self.statFrameRate)) + " frames/s")
		