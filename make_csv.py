import random
import pandas as pd
import csv

subject = ['전공', '교양', '일반']

a = [[random.randrange(1, 337), random.randrange(0,101),random.choice(subject)] for i in range(10000)]
f = open('study.csv', 'w', newline='')
data = a
writer = csv.writer(f)
writer.writerows(data)
f.close()

