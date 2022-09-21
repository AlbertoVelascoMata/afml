import dummy

from tqdm import tqdm
import sys
import time

for i in tqdm(range(10), desc='Progress', file=sys.stdout):
    time.sleep(1)
