import json


def from_file(path):
	try:  # try and use the normal json library and fall back to the custom one if comments are used
		with open(path) as f:
			return json.load(f)
	except:
		with open(path) as f:
			return loads(f.read())


def loads(_json):
	# given a valid MinecraftJSON string will return the values as python objects
	# in this context MinecraftJSON is standard JSON but with comment blocks and
	# line comments that would normally be illegal in standard JSON

	def stripWhitespace(_json, index):
		# skips whitespace characters (<space>, <tab>, <charrage return> and <newline>)
		# as well as block comments and line comments
		while _json[index] in ' \t\r\n':
			index += 1
		if _json[index] == '/':
			if _json[index + 1] == '/':
				index += 2
				while _json[index] != '\n':
					index += 1
				index = stripWhitespace(_json, index)
			elif _json[index + 1] == '*':
				index += 2
				while _json[index:index + 2] != '*/':
					index += 1
					if index + 1 >= len(_json):
						raise Exception('expected */ but reached the end of file')
				index += 2
				index = stripWhitespace(_json, index)
			else:
				raise Exception('unexpected / at index {}'.format(index))
		return index

	def parseJSONRecursive(_json, index=0):
		index = stripWhitespace(_json, index)
		if _json[index] == '{':
			index += 1
			# dictionary
			jsonObj = {}
			repeat = True
			while repeat:
				index = stripWhitespace(_json, index)
				# }"
				if _json[index] == '"':
					index += 1
					key = ''
					while _json[index] != '"':
						key += _json[index]
						index += 1
					index += 1

					index = stripWhitespace(_json, index)

					if _json[index] == ':':
						index += 1
					else:
						raise Exception('expected : got {} at index {}'.format(_json[index], index))

					index = stripWhitespace(_json, index)

					jsonObj[key], index = parseJSONRecursive(_json, index)

					index = stripWhitespace(_json, index)

					if _json[index] == ',':
						index += 1
					else:
						repeat = False
				else:
					repeat = False

			if index >= len(_json):
				raise Exception('expected } but reached end of file')
			elif _json[index] == '}':
				index += 1
			else:
				raise Exception('expected {} got {} at index {}'.format('}', _json[index], index))
			return (jsonObj, index)



		elif _json[index] == '[':
			index += 1
			# list
			jsonObj = []
			index = stripWhitespace(_json, index)
			repeat = _json[index] != ']'
			while repeat:
				val, index = parseJSONRecursive(_json, index)
				jsonObj.append(val)

				index = stripWhitespace(_json, index)

				if _json[index] == ',':
					index += 1
				else:
					repeat = False
				index = stripWhitespace(_json, index)

			if index >= len(_json):
				raise Exception('expected ] but reached end of file')
			elif _json[index] == ']':
				index += 1
			else:
				raise Exception('expected {} got {} at index {}'.format(']', _json[index], index))
			return (jsonObj, index)





		elif _json[index] == '"':
			index += 1
			# string
			jsonObj = ''
			while _json[index] != '"':
				jsonObj += _json[index]
				index += 1
			index += 1
			return (jsonObj, index)

		elif _json[index] in '0123456789-':
			# number
			jsonObj = ''
			while _json[index] in '0123456789-.':
				jsonObj += _json[index]
				index += 1
			if '.' in jsonObj:
				return (float(jsonObj), index)
			else:
				return (int(jsonObj), index)

		elif _json[index] == 'n' and _json[index:index + 4] == 'null':
			index += 4
			return (None, index)

		elif _json[index] == 't' and _json[index:index + 4] == 'true':
			index += 4
			return (True, index)

		elif _json[index] == 'f' and _json[index:index + 5] == 'false':
			index += 5
			return (False, index)
		else:
			raise Exception('unexpected key {} at {}. Expected {}, [, ", num, null, true or false'.format(_json[index], index, '{'))

	# call recursive function and pass back python object
	return parseJSONRecursive(_json)[0]


# given a python object will return the structured JSON text
def dumps(d, indent=0, initialIndent=True):
	obj = ''
	if initialIndent:
		obj += '  ' * indent
	if type(d) == dict:
		obj += '{\n'
		for n, key in enumerate(d):
			obj += '  ' * (indent + 1) + '"' + key + '" : '
			obj += dumps(d[key], indent + 1, initialIndent=False)
			if n + 1 != len(d):
				obj += ',\n'
			else:
				obj += '\n'
		obj += '  ' * indent + '}'
	elif type(d) == list:
		obj += '[\n'
		for n, value in enumerate(d):
			obj += dumps(value, indent + 1)
			if n + 1 != len(d):
				obj += ',\n'
			else:
				obj += '\n'
		obj += '  ' * indent + ']'
	elif type(d) == str:
		obj += '"{}"'.format(d)
	elif type(d) in [int, float]:
		obj += str(d)
	elif type(d) == bool:
		if d:
			obj += 'true'
		else:
			obj += 'false'
	elif d is None:
		obj += 'null'
	else:
		raise Exception('object of type {} is not supported'.format(type(d)))
	return obj