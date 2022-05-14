class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
			self.dataArr = []
			data = self.file.read(5) # Get the framelength from the first 5 bits
			while data: 
				framelength = int(data)
				# Read the current frame
				self.dataArr += [self.file.read(framelength)]
				data = self.file.read(5)
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self, backward):
		"""Get next frame."""
		if backward and self.frameNum>0:
			self.frameNum -= 1
		elif not backward and self.frameNum < len(self.dataArr)-1:
			self.frameNum += 1
		else: return None
		return self.dataArr[self.frameNum]
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	