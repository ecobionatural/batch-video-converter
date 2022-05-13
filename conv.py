# PREV: convlist.py
# INPUT: ./_convlist.txt
# OUTPUT: converted files in "./_conv" dir
# NEXT: none

# Convert files from _convlist.txt
# Run convlist.py first!

import sys
import os
import subprocess
import re
import json

def parsedim(dim):
	return list(map(lambda v: int(float(v)),dim.split('x')))
#
# tgtdir = sys.argv[1] if len(sys.argv) > 1 else '_conv';
# print(tgtdir)
#exit()
tgtdir = '_conv'

conffile = '_conv_conf.json'
if os.path.isfile(conffile):
	f = open(conffile,'r')
	c = json.loads(f.read())
	f.close()
	if('convdir' in c):
		tgtdir = c['convdir'];


print('tgtdir',tgtdir)
#exit();

if len(sys.argv) > 1:
	tgtdir = sys.argv[1]

if tgtdir and not os.path.isdir(tgtdir):
	os.mkdir(tgtdir)

if not os.path.isfile('_convlist.txt'):
	raise Exception('_convlist.txt not found')

lines = tuple(open('_convlist.txt','r'))

for l in lines:
	#lp = .split("\t")
	d = json.loads(l);

	sdim = parsedim(d['sdim'])
	tdim = parsedim(d['tdim'])


	if tgtdir:
		outfile = tgtdir+'/'+d['file'].replace('./','')
		os.makedirs(os.path.dirname(outfile),exist_ok=True)
	else:
		ext = d['file'].split('.')[-1]
		outfile = '.'.join(d['file'].split('.')[0:-1])+'.conv.'+ext\

	outfile = re.sub(r'(\.[^\.]+$)','.mp4',outfile)

	if os.path.isfile(outfile):
		print('SKIP',d['file'])
		continue

	if not os.path.isfile(d['file']):
		print('MISSING',d['file'])
		continue

	tmpname = re.sub(r'(\.[^\.]+$)',r'.tmp\1',outfile)
	if os.path.isfile(tmpname):
		os.remove(tmpname)

	cmd = 'ffmpeg -i "'+d['file']+'" -c:v libx264 -b:v '+str(d['tvb'])+'k -b:a 128k '
	if sdim[0] != tdim[0]:
		if tdim[1]%2 > 0:
			tdim[1] += 1
		cmd = cmd+' -vf scale='+str(tdim[0])+':'+str(tdim[1])+' '

	cmd = cmd+' "'+tmpname+'"'
	print(cmd)
	subprocess.run(cmd)
	os.rename(tmpname,outfile)
