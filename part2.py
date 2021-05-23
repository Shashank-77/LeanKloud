import numpy as np
import pandas as pd

df = pd.read_csv('Student_marks_list.csv')

for col in df.columns[1:]:
    max_ind = df[col].idxmax()
    print("Topper in {} is {}".format(col,df['Name'][max_ind]))

df['Total'] = df.sum(axis=1)

list_toppers = df.nlargest(3, ['Total'])['Name'].values
print("The top three Students in class in the following order are: {}, {}, {}".format(list_toppers[0], list_toppers[1], list_toppers[2]))

