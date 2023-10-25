import json
from numpy.random import normal
from random import uniform, choice, randint
colors = ['red', 'orange', 'yellow', 'lime', 'green', 'blue', 'purple', 'brown', 'black']

for i in range(1, 11):
    a = randint(0, 3)
    b = a + randint(1, 4)
    mi = randint(15, 30)
    sigma = randint(1, 5)
    with open(f'file{i}.txt', 'w') as f:
        for j in range(10000):
            color = choice(colors)
            uni = uniform(a, b)
            norm = normal(mi, sigma)
            val_dict = {'color': color, 'value1': uni, 'value2': norm}
            f.write(f'{val_dict}\n')

