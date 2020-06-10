def main():
	f = open("answers.txt", "r")
	count = 0
	for line in f:
		line = line.split()
		if line[1:] != []:
			count += 1
	print(count)
	
if __name__ == '__main__':
	main()
