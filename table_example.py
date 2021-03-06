# -*- coding: utf-8 -*-
from image2tokens import extractTokens, extractLines
from ocr import Ocr
import json
import os
import re
import sys
import numpy as np
import pandas as pd
import xlsxwriter

## UNICODE BLOCKS ##

# Regular expression unicode blocks collected from 
# http://www.localizingjapan.com/blog/2012/01/20/regular-expressions-for-japanese-text/

hiragana_full = ur'[ぁ-ゟ]'
katakana_full = ur'[゠-ヿ]'
kanji = ur'[㐀-䶵一-鿋豈-頻]'
radicals = ur'[⺀-⿕]'
katakana_half_width = ur'[｟-ﾟ]'
alphanum_full = ur'[！-～]'
symbols_punct = ur'[、-〿]'
misc_symbols = ur'[ㇰ-ㇿ㈠-㉃㊀-㋾㌀-㍿]'

def extract_unicode_block(string):
	#extract all unicode blocks for Chinese and Japanese text/symbols

	#we add all of the blocks detected into a list and export it
	unicode_block = []

	unicode_block.extend(re.findall(hiragana_full, string))
	unicode_block.extend(re.findall(katakana_full, string))
	unicode_block.extend(re.findall(kanji, string))
	unicode_block.extend(re.findall(radicals, string))
	unicode_block.extend(re.findall(katakana_half_width, string))
	unicode_block.extend(re.findall(alphanum_full, string))
	unicode_block.extend(re.findall(symbols_punct, string))
	unicode_block.extend(re.findall(misc_symbols, string))

	return unicode_block

def list_to_dataframe(output_list, y, x):
	#creating numpy array
	npdump = np.array(output_list)

	#creating dataframe of the array
	dataframe = pd.DataFrame(npdump.reshape(y,x))

	return dataframe, dataframe.style.set_properties(**{'text-align': 'left'})


def changeFileExtension(path,newExtension):
	res = ''.join(path.split(".")[:-1])+'.'+newExtension
	print(res)
	return res

def main(imagePath):
	# Create OCR
	ocr = Ocr()

	# Run OCR over image. It generates a JSON with the text and the coordinates of each word
	ocr.processFile(imagePath,'./')

	# Read JSON
	jsonFile = changeFileExtension(imagePath.split("/")[-1],"json")
	with open(jsonFile,'r') as f:
	    image = json.load(f)

	

	# Extract tokens (Each word, its width, height and its coordinates)
	tokens = extractTokens(image)

	# Sort the tokens into lines
	lines, x, y = extractLines(tokens)

	os.remove(jsonFile)

	output = []
	#txt = ""
	num_row = 0
	num_col = 0
	for line in lines:
		output.append(line)
		num_row += 1
		if (len(line) > num_col):
			num_col = len(line)

	dataframe, data = list_to_dataframe(output, y, x)



	writer = pd.ExcelWriter(os.path.splitext(imagePath)[0] + '.xlsx', engine='xlsxwriter', options={'strings_to_numbers': True})
	data.to_excel(writer, index=False, header=None, sheet_name='Sheet1')
	workbook = writer.book
	worksheet = writer.sheets['Sheet1']

	for column in dataframe:
		max_length = 0
		adjustment = 1
		for i in dataframe[column]:
			
			#get number of chinese and japanese characters/symbols in string
			east_asian_text_adj = len(extract_unicode_block(i))

			#adjust column_length by the amount of normal eng chars + jpn/chn chars
			column_length = len(i) + east_asian_text_adj
			if column_length > max_length:
				max_length = column_length
				
		col_idx = dataframe.columns.get_loc(column)
		writer.sheets['Sheet1'].set_column(col_idx, col_idx, max_length)
	
	writer.save()

	dataframe.to_csv(os.path.splitext(imagePath)[0] + '.csv', index=False, header=False,encoding='utf-8-sig')
		#print(line)
		
		#line = list(filter(lambda x : x != '-',line))
		
		#for words in line:
		#	txt += words
                
		#txt += "\n"  
		

	#with open(changeFileExtension(imagePath.split('/')[-1],'txt'),'w') as f:
		#f.write(txt)

imagePath = sys.argv[1]
print('RUNNING ON ' + imagePath)
main(imagePath)
#detect_text(imagePath)


