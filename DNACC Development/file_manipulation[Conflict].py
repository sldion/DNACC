	
file = open('data.txt', 'w+')

x = [1,2,3,4]

file.write(str(x))
y = []

for line in file:
	y = int(file.readline())

	y.append(5)


file.write(str(y))

