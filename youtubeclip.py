import numpy as np
import matplotlib.pyplot as plt
from pytube import YouTube
import os
import subprocess
from scipy.io import wavfile
import json
import googleapiclient.discovery
import re
import pandas as pd
from timestamps import split_timestamps, convert_timestamp, overlap, merge
import csv
from movie_maker import create_video_clips
from scipy.ndimage import generic_filter as gf
from scipy.signal import find_peaks

PATTERN = re.compile(r'\d{1,3}(?::\d{1,3}){1,2}(?:\s*-\s*\d{1,3}(?::\d{1,3}){1,2})?')
TIMESTAMP_MULTIPLIER = 2

def argmin_min_within_length(data, start, length):
	if length>0:
		length = min(len(data)-1-start,length)
	full_val = np.max(data)+1
	window = np.full_like(data,full_val)
	if length>0:
		window[start:start+length+1] = data[start:start+length+1]
	else:
		window[start+length:start+1] = data[start+length:start+1]
	if length<0:
		window = np.flip(window)
		return len(window)-1-np.argmin(window), np.min(window)
	return np.argmin(window), np.min(window)

def argmin_min_within_range(data,start,end):
	if start<end:
		tmp = end
		end = start
		start = tmp
	data = data[start:end]
	return np.argmin(data), np.min(data)


class YoutubeVideo():
	def __init__(self, *args, **kwargs):

		self.url = kwargs.get('url',None)
		if self.url:
			self.id_ = self.url[self.url.index('.com/watch?v=')+len('.com/watch?v='):]
		else:
			self.id_ = kwargs.get('id_',None)
			self.url = 'https://www.youtube.com/watch?v=' + self.id_
		if not self.url:
			raise ValueError('Please provide a url or id to your video.')

		self.plot_color = kwargs.get('plot_color', [66/255.,78/255.,245/255.])
		self.delta_t = kwargs.get('delta_t',10)
		self.audio_delta_t = kwargs.get('audio_delta_t',.5)
		self.max_len = kwargs.get('max_len',60)

		self.playlist_folder = kwargs.get('playlist_folder','separateVideos')

		print('Getting data now')
		yt = YouTube(self.url)
		self.original_title = yt.title
		self.title = self.clean_title(self.original_title)
		self.comments_path = self.download_comments()
		self.video_path = self.download_video(yt)
		self.audio_path = self.download_audio(yt)
		self.wav_path = self.extract_wav()
		self.dbs = self.get_dbs()
		self.length = yt.length
		self.views = yt.views
		self.gti = self.find_good_timeintervals(user_gen_quantile=.9, plot_kernels=False, fix_discrepancies=True)

		

	def set_plot_color(self, color):
		self.plot_color = color
	def clean_title(self,title):
		return title.replace('<','').replace('>','') \
		.replace(':','').replace('"','').replace('/','') \
		.replace('\\','').replace('|','').replace('?','') \
		.replace('*','').replace('.','').replace(',','') \
		.replace('~','').replace('\'','').replace('$','')
	
	def download_video(self, yt):
		self.length = yt.length
		self.views = yt.views
		video = yt.streams.filter(progressive=False,file_extension='mp4').order_by('resolution').desc().first()
		self.title = self.clean_title(yt.title)
		vid_filepath = os.path.join(f'./playlists/{self.playlist_folder}/videos/',self.title+'.mp4')
		if not os.path.exists(vid_filepath):
			print('Downloading video of {} with format {}'.format(self.title, video))
			video.download(f'./playlists/{self.playlist_folder}/videos')
		else:
			print('Video of {} already downloaded.'.format(self.title))
		return vid_filepath

	def download_audio(self, yt):
		audio = yt.streams.filter(only_audio=True).first()
		self.title = self.clean_title(yt.title)
		aud_filepath = os.path.join(f'./playlists/{self.playlist_folder}/audio/',self.title+'.mp4')
		if not os.path.exists(aud_filepath):
			print('Downloading audio of {} with format {}'.format(self.title, audio.mime_type))
			audio.download(f'./playlists/{self.playlist_folder}/audio')
		else:
			print('Audio of {} already downloaded.'.format(self.title))
		return aud_filepath

	def extract_wav(self):
		if not os.path.exists(os.path.join(f'./playlists/{self.playlist_folder}/wavs/',self.title+'.wav')):
			command = 'ffmpeg -hide_banner -loglevel error -i "./{}" -ab 160k -ac 2 -ar 44100 -vn "./playlists/{}/wavs/{}.wav"'.format(self.audio_path, self.playlist_folder, self.title)
			subprocess.call(command, shell=True)
			print('Created WAV file.')
		else:
			print('WAV File already exists.')
		return os.path.join(f'./playlists/{self.playlist_folder}/wavs/',self.title+'.wav')

	def get_dbs(self):
		samplerate, data = wavfile.read(self.wav_path)
		self.length = data.shape[0] / samplerate
		chunk_size = round(samplerate * self.audio_delta_t)
		self.num_chunks = data.shape[0] // chunk_size

		data_chunks = np.array_split(data, self.num_chunks)
		means = [np.mean(chunk**2) for chunk in data_chunks]
		dbs = [20*np.log10(np.sqrt(mean)) if mean > 0 else 0 for mean in means]
		return dbs

	def set_delta_t(self,delta_t):
		self.delta_t = delta_t

	def set_audio_delta_t(self, audio_delta_t):
		self.audio_delta_t = audio_delta_t

	def get_timestamps(self):
		timestamps = []
		with open(self.comments_path,'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			self.num_comments = sum(1 for row in reader)
		with open(self.comments_path,'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			for row in reader:
				try:
					comment = ''.join(row)
					[timestamps.append(ts) for ts in split_timestamps(re.findall(PATTERN, comment))]
				except Exception as e:
					pass
		return timestamps

	def timestamps_timeintervals(self):
		timestamps = self.get_timestamps()
		timestamps, timeintervals = [t for t in timestamps if type(t)!=list], [t for t in timestamps if type(t)==list]
		for ti in timeintervals:
			[[timestamps.append(t) for _ in range(TIMESTAMP_MULTIPLIER)] for t in range(ti[0],ti[1]+10,10)]
		return timestamps, timeintervals

	def remove_illegal_timeintervals(self, ts, max_len):
		ts_new = []
		for t in ts:
			if t[1] - t[0] <= max_len and t[0]>=0 and t[1]<self.length:
				ts_new.append(t)
		return ts_new

	def create_histogram(self, plot_graph=False, normalize=False, *args, **kwargs):
		timestamps, timeintervals = self.timestamps_timeintervals()
		timeintervals = self.remove_illegal_timeintervals(timeintervals, self.max_len)
		hist, bins = np.histogram(timestamps, bins=np.arange(0,self.length,self.delta_t))
		if normalize:
			hist = hist.astype(np.float32)/self.num_comments
		if plot_graph:
			self.plot(timestamps, timeintervals, *args, **kwargs)
			plt.gca().set_facecolor((.3,.3,.3))
		return hist, bins

	def group_kernel_indices(self,data,patience):
		groups = []
		diff = np.diff(data)
		t0 = None
		t1 = None
		#print('Diff:',diff)
		for i,d in enumerate(diff[~np.isnan(diff)]):
			if d<=patience*self.delta_t:
				if not t0:
					t0 = i
				t1 = i
			else: # d>patience so end timeinterval
				if t0:
					#print(f'Element {i} in diff = {d}, so t0 has been set to {t0} and t1 now set to {t1}.')
					groups.append([t0,t1])
					t0 = None
					t1 = None
		if t0 and t1 and t0!=t1:
			groups.append([t0,t1])
		return groups

	def plot(self, timestamps, timeintervals, plot_kernel=True, *args, **kwargs):
		dbs = self.dbs
		offset = kwargs.get('offset',0)
		quantile = kwargs.get('quantile',None)
		time = np.linspace(offset,self.length+offset,self.num_chunks)

		max_dbs = np.amax(dbs) # min-max normalization
		min_dbs = np.amin(dbs)
		dbs = (dbs - min_dbs)*20 / (max_dbs - min_dbs)

		plt.plot(time,dbs,c='w',linewidth=.5,alpha=.5)
		#plt.hlines(np.mean(dbs),0,time[-1],color='k')
		#plt.bar(bins[:-1], hist, color=self.plot_color)
		plt.hist([(t+offset) for t in timestamps],bins=np.arange(offset,self.length+offset,self.delta_t),color=self.plot_color)

		for i,interval in enumerate(timeintervals):
			plt.plot([(val+offset) for val in interval],[i+1]*len(interval),marker='o',c=self.plot_color,
				markersize=2,markeredgecolor='k',alpha=.8,label='User time intervals')

		if self.gti:
			for i,interval in enumerate(self.gti):
				plt.plot([(val+offset) for val in interval],[i+1.2]*len(interval),marker='o',c='r',
					markersize=2,markeredgecolor='k',alpha=.8,label='Final time intervals')
		if plot_kernel:
			hist, bins = np.histogram([t for t in timestamps],bins=np.arange(0,self.length,self.delta_t))
			convolution = np.convolve(hist,np.ones(8,dtype=int),'same')
			height = np.quantile(convolution, .8)
			#indices = find_peaks(convolution, height=height, distance=4)[0]
			indices = np.where(convolution>=height)[0]
			plt.hlines(height,offset,self.length+offset,alpha=.5,color='k')
			plt.plot(np.arange(offset,len(hist)*self.delta_t+offset,self.delta_t),convolution,color=self.plot_color)
			plt.plot(np.multiply(indices,self.delta_t)+offset,convolution[indices],'x',color=self.plot_color)
		handles, labels = plt.gca().get_legend_handles_labels()
		by_label = dict(zip(labels, handles))
		plt.legend(by_label.values(), by_label.keys(),loc='upper right')


	def find_good_timeintervals(self, user_gen_quantile=.8,
								algorithmic_gen_quantile=.8,
								max_walkback=15, max_walkforward=10, 
								min_walkback=1, min_walkforward=1,
								val=None, plot_kernels=False, fix_discrepancies=True):
		dbs = self.dbs
		timestamps, timeintervals = self.timestamps_timeintervals()
		timeintervals = self.remove_illegal_timeintervals(timeintervals, self.max_len)
		hist, bins = np.histogram([t for t in timestamps],bins=np.arange(0,self.length,self.delta_t))
		hist = hist.astype(np.float16)/self.views
		
		if plot_kernels:
			fig, axs = plt.subplots(4,1, sharey=True)
			plt.title('Timestamp Histogram with Convolution Sum')
			for i,ax in enumerate(axs):
				convolution = np.convolve(hist,np.ones(2**i,dtype=int),'same')
				ax.plot(convolution)
				height = np.quantile(convolution, algorithmic_gen_quantile)
				ax.plot(np.arange(len(convolution)),[height]*len(convolution),color='green')
				indices = find_peaks(convolution,height=height, distance=4)[0]
				ax.plot(indices,convolution[indices],'x')
				ax.set_ylabel('kernel_size={}'.format(2**i),rotation=0)
			
			plt.show()
			fig, axs = plt.subplots(4,1,sharey=True)
			plt.title('Volume with Convolution Sum')
			for i,ax in enumerate(axs):
				convolution = np.convolve(dbs[:60*4],np.ones(2**i,dtype=int),'same')
				convolution = (convolution - np.mean(convolution)) / np.std(convolution)
				ax.plot(convolution)
				indices = find_peaks(convolution)[0]
				#ax.plot(indices,convolution[indices],'x')
				ax.set_ylabel('kernel_size={} ({}sec)'.format(2**i,(2**i)/4),rotation=0)
			
			plt.show()

		if not val:
			val = np.quantile(hist, user_gen_quantile)

		good_bins = bins[:-1][hist>=val]
		user_gen = []
		for good_bin in good_bins:
			adjusted_tis = []
			for ti in timeintervals:
				if good_bin>=ti[0] and good_bin<ti[1]:
					original_start, original_end = ti[0], ti[1]
					delta_t_reciprocal = round(self.audio_delta_t**-1)
					start, _ = argmin_min_within_length(dbs,(original_start-min_walkback)*delta_t_reciprocal,delta_t_reciprocal*-max_walkback)
					end, _ = argmin_min_within_length(dbs,(original_end+min_walkforward)*delta_t_reciprocal,delta_t_reciprocal*max_walkforward)
					start/=delta_t_reciprocal
					end/=delta_t_reciprocal
					adjusted_tis.append([start,end])
					#print(f'[{ti[0]},{ti[1]}] -> [{start},{end}]')
			if len(adjusted_tis)>0:
				minimum, maximum = np.min([t[0] for t in adjusted_tis]), np.max([t[1] for t in adjusted_tis])
				if maximum-minimum<=self.max_len:
					user_gen.append([np.min([t[0] for t in adjusted_tis]), np.max([t[1] for t in adjusted_tis])])
		#print(good_bins)
		convolution = np.convolve(hist,np.ones(8,dtype=int),'same')
		height = np.quantile(convolution, algorithmic_gen_quantile)
		indices = np.where(convolution>=height)[0]
		good_bins = bins[indices]
		#print('Good bins:',good_bins)
		group_start_end_indices = self.group_kernel_indices(good_bins,2)
		#print('Group start and end indices:', group_start_end_indices)
		algo_gen = []
		for group in group_start_end_indices:
			ti = [good_bins[group[0]],good_bins[group[1]]+10]
			#print('Group start and end times:', ti)
			original_start, original_end = ti[0], ti[1]
			delta_t_reciprocal = round(self.audio_delta_t**-1)
			start, _ = argmin_min_within_length(dbs,(original_start-min_walkback)*delta_t_reciprocal,delta_t_reciprocal*-max_walkback)
			end, _ = argmin_min_within_length(dbs,(original_end+min_walkforward)*delta_t_reciprocal,delta_t_reciprocal*max_walkforward)
			start/=delta_t_reciprocal
			end/=delta_t_reciprocal
			algo_gen.append([start,end])
		#print('Algorithmicaly generated:',algo_gen)
		if fix_discrepancies:
			final = self.fix_discrepancies(user_gen,algo_gen)
			return final
		else:
			return user_gen+algo_gen

	def fix_discrepancies(self, user_gen, algo_gen):
		gen_methods = {}
		for i, u in enumerate(user_gen):
			gen_methods[tuple(u)] = [i,True]
		for i, a in enumerate(algo_gen):
			gen_methods[tuple(a)] = [i,False]
		concat = user_gen + algo_gen
		for bin_ in range(0,self.length,self.delta_t):
			ti = self.timeintervals_intersect_bin(bin_,concat)
			ti = [[i,t] for i,t in enumerate(ti)]
			result = None
			if len(ti)==1:
				result = ti[0]
			elif len(ti)>1: # multiple ti intersect this bin
				for t in ti:
					if gen_methods[tuple(t[1])][1]: # if is user gen
						result = t
						break
				if not result:
					result = ti[0]
			if result:
				for t in ti:
					if t != result:
						concat.remove(t[1])
		#return [x for x in concat if x not in ans]
		return concat
	
	def timeintervals_intersect_bin(self, bin_, timeintervals):
		return [t for t in timeintervals if t[0]<=bin_ and t[1]>bin_]


	def fitting_timeintervals(self,ti,start_range=None,end_range=None):
		if start_range is not None and end_range is not None:
			return [t for t in ti 
					if t[0]>=start_range[0] and t[0]<=start_range[1]
					and t[1]>=end_range[0] and t[1]<=end_range[1]]
		elif start_range is not None:
			return [t for t in ti 
					if t[0]>=start_range[0] and t[0]<=start_range[1]]
		elif start_range is None and end_range is None:
			return None
		else:
			return [t for t in ti 
					if t[1]>=end_range[0] and t[1]<=end_range[1]]

	def download_comments(self, max_pages=100):
		filename = os.path.join(f'./playlists/{self.playlist_folder}/comments/',self.title+'.csv')
		if os.path.exists(filename):
			print('Comments already downloaded.')
			return filename
		print('Grabbing comments now...')
		# Disable OAuthlib's HTTPS verification when running locally.
		# *DO NOT* leave this option enabled in production.
		#os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
		comments = []
		api_service_name = "youtube"
		api_version = "v3"
		DEVELOPER_KEY = "AIzaSyAn5ykH3EZSXZ5VPfGJ5ncWJQGIOmmCzVI"

		youtube = googleapiclient.discovery.build(
			api_service_name, api_version, developerKey = DEVELOPER_KEY)
		request = youtube.commentThreads().list(
			part="snippet,replies",
			videoId=self.id_,
			maxResults=100
		)
		response = request.execute()
		for c in response['items']:
			comments.append(c['snippet']['topLevelComment']['snippet']['textOriginal'])
		#print(comments)
		nextToken = response.get('nextPageToken', None)
		i = 1
		while nextToken and i<max_pages:
			request = youtube.commentThreads().list(
				part="snippet",
				videoId=self.id_,
				maxResults=100,
				pageToken=nextToken
			)
			response = request.execute()
			for c in response['items']:
				comments.append(''.join(c['snippet']['topLevelComment']['snippet']['textOriginal']))
			try:
				nextToken = response['nextPageToken']
			except:
				break
			print(f'Page {i}/{max_pages}', end='\r')
			i+=1
		with open(filename,'w', encoding='utf-8') as f:
			writer = csv.writer(f)
			for comment in comments:
				#print(comment)
				writer.writerow(comment)
		return filename

if __name__ == '__main__':
	yt = YoutubeVideo(url='https://www.youtube.com/watch?v=SFTxiJ3CyQY&list=PL9XS3v3WZxjbsFEj-1QBTcJdkBc8rL3X-', audio_delta_t=.25)
	print('Good Time Intervals:', yt.gti)
	yt.set_plot_color([66/255.,135/255.,245/255.])
	yt.create_histogram(plot_graph=True)
	plt.show()
	create_video_clips(yt.video_path,yt.audio_path,yt.gti,'./playlists/Game Grumps - Kirby Dream Course/clips/0.mp4', overlay_text=yt.original_title)