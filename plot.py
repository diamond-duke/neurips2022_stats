import os
from tqdm import trange
from operator import itemgetter
import numpy as np
from pprint import pprint

import matplotlib.pyplot as plt
from matplotlib import rc
gridc = (1., 1., 1)
plt.rcParams['grid.color'] = gridc
plt.rcParams["axes.edgecolor"] = (0.898, 0.925, 0.965, 1)
plt.rc('xtick', labelsize=12)
plt.rc('ytick', labelsize=12)

from database import DataBase
db = DataBase('assets/neurips2022.db')
db.initialize()

# all decisions
_cmd = "SELECT rating_avg FROM submissions;"
db.cursor.execute(_cmd)
data = db.cursor.fetchall()
rating_avgs = np.array(data)
print("> Total submissions (including CE): {}".format(len(data)))
print(f"    Average ratings: {rating_avgs.mean():.2f}")
print(f"    Max ratings: {rating_avgs.max():.2f}")
print(f"    Min ratings: {rating_avgs.min():.2f}")

_min, _max = rating_avgs.min(), rating_avgs.max()

width = 0.16
fig = plt.figure(figsize=[16, 6])

ax = fig.add_subplot(1, 1, 1)
ax.set_facecolor((0.898, 0.925, 0.965, 0.5))
ax.spines['left'].set_color('w')
ax.spines['bottom'].set_color('w')
ax.spines['right'].set_color('w')
ax.spines['top'].set_color('w')

# all submissions
hist, bin_edges = np.histogram(rating_avgs, bins=20, range=(_min, _max))
ax.bar(np.linspace(_min, _max, len(hist)), hist, width=width, alpha=0.95, 
       color='#789BFF', capsize=4)
for i, v in zip(np.linspace(_min, _max, len(hist)), hist):
    ax.text(i - 0.1 if v >= 100 else i - 0.05, v + 6.0, str(v), color='#1f59ff', fontsize=16)

plt.ylim(0, 550)
plt.xticks(ticks=np.linspace(_min, _max, len(hist)), 
           rotation=40, 
           labels=[f"{d:.2f}" for d in np.linspace(_min, _max, len(hist))])
ax.set_ylabel(r"# submissions", fontsize=14)
ax.set_xlabel("Rating", fontsize=14)
ax.set_axisbelow(True)
ax.grid()
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[::-1], labels[::-1], loc=2, fontsize=14)
plt.savefig('assets/stats_bar.png')
