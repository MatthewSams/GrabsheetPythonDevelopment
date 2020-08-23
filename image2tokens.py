import os
import sys
import numpy as np
from google.oauth2 import service_account

reload(sys)
sys.setdefaultencoding('utf8')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credential.json"

class Token():
    def __init__(self,x,y,width,height,text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

def extractTokens(image):
	tokens = []

	for page in image['fullTextAnnotation']['pages']:
	    for block in page["blocks"]:
	        for paragraph in block["paragraphs"]:
	            text = ""
	            firstWord = paragraph["words"][0]

	            i = 1
	            n = len(paragraph["words"])
	            for word in paragraph["words"]:
	                lastWord = word

	                breakType = None
	                if len(word["symbols"]) > 0 and "property" in word["symbols"][-1] and "detectedBreak" in word["symbols"][-1]["property"]:
	                    breakType = word["symbols"][-1]["property"]["detectedBreak"];

	                for symbol in word["symbols"]:
	                    text += symbol["text"]

	                if breakType != None:# and breakType in ["LINE_BREAK",""]:
	                    vertices = firstWord["boundingBox"]["vertices"]
	                    minX = vertices[0]["x"]
	                    minY = vertices[0]["y"]
	                    maxY = vertices[3]["y"]
	                    vertices = lastWord["boundingBox"]["vertices"]
	                    maxX = vertices[1]["x"]

	                    newToken = Token(minX, maxY, maxX - minX, maxY - minY, text)
	                    tokens.append(newToken)


	                    text = ""
	                    if i < n:
	                        firstWord = paragraph["words"][i];

	                i += 1
	return tokens

def initialize_lines(tokens):
	newLine = []
	lines = []

	newLine.append(tokens[0])
	lastY = tokens[0].y
	lastX = tokens[0].x + tokens[0].width
	return newLine, lines, lastY, lastX

def get_midpoint(tokens):
	MAX_SPACE_BETWEEN_WORDS = 30

	tokens = sorted(tokens, key=lambda token : token.x)

	last = tokens[0]
	midpoint = []
	textblock_x = 0
	count = 0

	for token in tokens[1:]:
		if token.x - (last.x + last.width) > MAX_SPACE_BETWEEN_WORDS:
			count += 1
			textblock_x = (textblock_x + (last.x + last.width/2))/count

			midpoint.append(textblock_x)
			textblock_x = 0
			count = 0
		else:
			count += 1
			textblock_x = (textblock_x + (last.x + last.width/2))
			

		last = token

	if textblock_x:
		count += 1
		midpoint.append((textblock_x + (tokens[-1].x + last.width/2))/count)
	else:
		midpoint.append(tokens[-1].x + tokens[-1].width/2)

	return midpoint


def createLine(tokens):
	MAX_SPACE_BETWEEN_WORDS = 30

	tokens = sorted(tokens, key=lambda token : token.x)

	last = tokens[0]
	texts = []
	textblock = ""
	textblock_x = 0
	count = 0

	for token in tokens[1:]:
		if token.x - (last.x + last.width) > MAX_SPACE_BETWEEN_WORDS:
			count += 1
			textblock = textblock + last.text
			#textblock_x = (textblock_x + (last.x + last.width/2))/count

			texts.append((textblock_x, textblock))

			textblock = ""
			textblock_x = 0
			count = 0
		else:
			count += 1
			textblock = textblock + last.text + " "
			if count == 1:
				textblock_x = ((last.x + last.width/2))
			#textblock_x = (textblock_x + (last.x + last.width/2))

		last = token

	if textblock:
		count += 1
		#texts.append(((textblock_x + (tokens[-1].x + last.width/2))/count, textblock + tokens[-1].text))
		texts.append((textblock_x, textblock + tokens[-1].text))
	else:
		texts.append((tokens[-1].x + tokens[-1].width/2, tokens[-1].text))

	return texts

def get_maxcolnum_midpoint(newLine, maxcol_num, midpoint):
	max_column = get_midpoint(newLine)
	if (len(max_column) > maxcol_num):
		#print('midpoint: ')
		#print(len(max_column))
		#print(maxcol_num)
		return len(max_column), max_column
	else:
		return maxcol_num, midpoint

def check_index(lis, ind):
	down = ind
	up = ind

	while (lis[ind] != ''):
		if (down - 1 >= 0):
			down = down - 1
			#print(down)
			if (lis[down] == ''):
				return down
		if (up + 1 < len(lis)):
			up = up + 1
			#print(up)
			if (lis[up] == ''):
				return up


def extractLines(tokens):
	tokens = sorted(tokens, key=lambda token : token.y)


	#initialize empty variables so we can iterate through the tokens
	newLine, lines, lastY, lastX = initialize_lines(tokens)

	#by looking at each row, identifies the max amount of columns present. 
	#use this to set dimensions of excel sheet
	maxcol_num = 0
	#mid point of the columns in that particular row
	midpoint = []
	#number of columns in document. starts at 1 to account for the last line.
	num_col = 1

	for token in tokens[1:]:
	    if token.y > lastY + token.height * 0.6:
	        lines.append(createLine(newLine))
	        maxcol_num, midpoint = get_maxcolnum_midpoint(newLine, maxcol_num, midpoint)

	        lastY = token.y
	        newLine = []

	        num_col += 1

	    newLine.append(token)
	    lastX = token.x + token.width

	lines.append(createLine(newLine))
	maxcol_num, midpoint = get_maxcolnum_midpoint(newLine, maxcol_num, midpoint)

	#print(lines)

	midpoint = np.array(midpoint)
	midpoint.sort()

	final_list = []

	for i in range(num_col):
		lis = [ '' for k in range(len(midpoint))]
		for index in lines[i]:
			diff = abs(midpoint - index[0])
			minvalue = min(diff)
			ind = list(diff).index(minvalue)

			if lis[ind] == '':
				lis[ind] = index[1]
			else:
				#print('original')
				#print(ind)
				#print(lis[ind])
				new_ind = check_index(lis, ind)
				#print(new_ind)
				lis[new_ind] = index[1]


		final_list.extend(lis)


	#print('finallist')
	#print(final_list)

	return final_list, len(midpoint), num_col
