# PREV: none
# INPUT: current directory context
# OUTPUT: _convlist.txt - a list to convert
# NEXT: conv.py
# REQ: Python 3, FFMPEG

# Recursively search working dir and subdirs for video files
# receiving meta data of each video (resolution, bitrate)
# File will be added to conversion list if:
# 	a. Bitrate of video is too large for its resolution
#	b. Video is not MP4, WEBM or OGG (not playable in browser)
# Conversion list saved to file _convlist.txt inside working dir.
# You can edit that list if necessary.
# To start conversion, run "conv.py" afterwards

import os
import re
import subprocess
import json

allowed_extensions = ('mp4','mpeg4','webm','ogg')

#presets for dimension-to-bitrate decision
presets = {
	"high": {
		#if LARGEST side > 1920px -> convert with video bitrate 3000kbps
		"1920": 3000,
		"1280": 2000,
		"800": 1300,
		"0": 1000
	},
	"mid": {
		"1920": 2800,
		"1280": 1800,
		"800": 1100,
		"0": 800
	},
	"low": {
		"1920": 2000,
		"1280": 1500,
		"800": 1000,
		"0": 800
	}
}

# default config
# You can override this config by placing file _conv_conf.json in any folder.
# That will work for given folder and all subfolders recursively.
c_ = {
	"max_rate": 0.7,		# max relation of converted size to original size
	"max_side_size": 1280,	# max not-resizable size of LARGEST side
	"preset": "mid",
	"convdir": "./_conv"
}


cache = {}

def dive(dir,files,conf):
	ff = os.listdir(dir)
	new_conf = get_conf(dir,conf)
	for f in ff:
		full = dir+'/'+f
		if f[0:1]!='_' and os.path.isdir(full) and not os.path.isfile(full+'/.noconv'):
			dive(full,files,new_conf)
		else:
			files.append([full,new_conf])

def ffmpeg_info(file):
	pp = subprocess.Popen('ffmpeg -i "'+file+'"',shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE);
	s = pp.stderr.read();

	mm = re.findall('(Video\:.+?|bitrate\: )(\d+)\s*kb/s',str(s))
	mm.sort(key=lambda m:int(m[1]),reverse=True)
	vb = int(mm[0][1])

	mm = re.findall('(\d{3,4})x(\d{3,4})',str(s))
	mm.sort(key=lambda k: int(k[0]),reverse=True)
	dim = mm[0] if len(mm) > 0 else [0,0]
	size = int(os.stat(file).st_size)
	return {'vb':vb,'dim':dim,'size':size}

def get_video_info(file):
	size = int(os.stat(file).st_size)
	if file not in cache or cache[file]['size'] != size:
		cache[file] = ffmpeg_info(file)
	return cache[file]

def read_json(file):
	f = open(file,'r')
	data = json.loads(f.read())
	f.close()
	return data

def get_conf(dir,cur_conf):
	fname = dir+'/_conv_conf.json'
	print(f'checking {fname}')
	if not os.path.isfile(fname):
		return prep_conf(cur_conf)

	conf = read_json(fname)
	c = cur_conf | conf
	return prep_conf(c)

def prep_conf(c):
	if 'rates' not in c:
		c['rates'] = presets[c['preset']]
	return c


if os.path.isfile('_convlist_cache.json'):
	cache = read_json('_convlist_cache.json')


ff = []
dive('.',ff,c_)
ff = list(filter(lambda v: re.search('(?<!\.conv)\.(mpe?g|mp4|mkv|avi|flv|mov|wmv)$',v[0].lower()),ff))
out = []

cnt=0
for item in ff:
	[file,c] = item
	print(file,'...')
	dir = os.path.dirname(file)
	name,ext = os.path.splitext(file)

	v = get_video_info(file)

	vb = v['vb']
	tvb = vb
	w = int(v['dim'][0])
	h = int(v['dim'][1])
	max_side = max(w,h)
	ar = w/h if h else 1

	tw = w
	th = h

	if c['max_side_size'] and max_side > c['max_side_size']:
		if w==max_side:
			tw = c['max_side_size']
			th = int(tw/ar)
		else:
			th = c['max_side_size']
			tw = th*ar

	tresol = tw*th
	t_max_side = max(tw,th)

	for key in c['rates']:
		if t_max_side >= int(key):
			tvb = c['rates'][key]
			break

	compress_rate = 0
	compress_gain = 0
	compress = 0
	if vb > 0:
		compress_rate = tvb/vb
		compress_gain = 1-compress_rate
		gain = round(v['size']*compress_gain/1024/1024,1)

	if (ext not in allowed_extensions) or (compress_rate and compress_rate < c['max_rate']):
		data = {
			"file": file,
			"sdim": str(w)+'x'+str(h),
			"tdim": str(tw)+'x'+str(th),
			"svb": vb,
			"tvb": tvb,
			"gain_mb": compress,
			"crate": round(compress_rate,2)
		}
		s = file+'	'
		for i in data:
			#s += i+'='+str(data[i])+'; '
			s = json.dumps(data)

		out.append([s,compress])

	cnt+=1

out.sort(key=lambda v: v[1],reverse=True)
fp = open('./_convlist.txt','w')
fp.write('\n'.join(map(lambda v: v[0],out)))
fp.close()

fp = open('./_convlist_cache.json','w')
fp.write(json.dumps(cache))
fp.close()
print('File convlist.txt written')
