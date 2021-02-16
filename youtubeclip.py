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
from timestamps import split_timestamps, convert_timestamp

PATTERN = re.compile(r'\d{1,3}(?::\d{1,3}){1,2}(?:\s*-\s*\d{1,3}(?::\d{1,3}){1,2})?')

class YoutubeVideo():
	def __init__(self, *args, **kwargs):
		if 'url' in kwargs:
			self.url = kwargs['url']
			self.id_ = self.url[kwargs['url'].index('.com/watch?v=')+len('.com/watch?v='):]
			self.id_ = self.id_.split('&')[0]
		elif 'id' in kwargs:
			self.url = 'https://youtube.com/watch?v=' + kwargs['id']
			self.id_ = kwargs['id']
		else:
			raise ValueError('Please provide a url or id to your video.')

		if 'plot_color' in kwargs:
			self.plot_color = kwargs['plot_color']
		else:
			self.plot_color = [66/255.,78/255.,245/255.]

		self.delta_t = 10
		self.comments = None
		self.timestamps = None
		self.timeintervals = None
		self.dbs = None
		self.length = 0

		self.video_path = self.download_video()
		self.audio_path = self.download_audio()
		self.wav_path = self.extract_wav()
		

	def set_plot_color(self, color):
		self.plot_color = color
	def clean_title(self,title):
		return title.replace('<','').replace('>','') \
		.replace(':','').replace('"','').replace('/','') \
		.replace('\\','').replace('|','').replace('?','') \
		.replace('*','').replace('.','').replace(',','') \
		.replace('~','')
	
	def download_video(self):
		yt = YouTube(self.url)
		self.length = yt.length
		self.views = yt.views
		video = yt.streams.filter(progressive=False,file_extension='mp4').order_by('resolution').desc().first()
		self.title = self.clean_title(yt.title)
		self.vid_filepath = os.path.join('YTVideos',self.title+'.mp4')
		if not os.path.exists(self.vid_filepath):
			print('Downloading video of {} with format {}'.format(self.title, video))
			video.download('./YTVideos')
		else:
			print('Video of {} already downloaded.'.format(self.title))
		return self.vid_filepath

	def download_audio(self):
		yt = YouTube(self.url)
		audio = yt.streams.filter(only_audio=True).first()
		self.title = self.clean_title(yt.title)
		self.aud_filepath = os.path.join('YTAudio',self.title+'.mp4')
		if not os.path.exists(self.aud_filepath):
			print('Downloading audio of {} with format {}'.format(self.title, audio.mime_type))
			audio.download('./YTAudio')
		else:
			print('Audio of {} already downloaded.'.format(self.title))
		return self.aud_filepath

	def extract_wav(self):
		if not os.path.exists(self.audio_path):
			self.audio_path = self.download_audio()
		if not os.path.exists(os.path.join('wavs',self.title+'.wav')):
			command = 'ffmpeg -hide_banner -loglevel error -i "./{}" -ab 160k -ac 2 -ar 44100 -vn "./wavs/{}.wav"'.format(self.audio_path, self.title)
			print(command)
			subprocess.call(command, shell=True)
			print('Created WAV file.')
		else:
			print('WAV File already exists.')
		return os.path.join('wavs',self.title+'.wav')

	def get_dbs(self):
		print('TITLE:',self.title)
		if not os.path.exists(os.path.join('wavs',self.title+'.wav')):
			self.extract_wav()
		samplerate, data = wavfile.read(self.wav_path)
		self.length = data.shape[0] / samplerate
		chunk_size = samplerate*self.delta_t
		self.num_chunks = data.shape[0] // chunk_size

		data_chunks = np.array_split(data, self.num_chunks)
		dbs = [20*np.log10(np.sqrt(np.mean(chunk**2))) for chunk in data_chunks]
		return dbs

	def set_delta_t(self,delta_t):
		self.delta_t = delta_t

	def get_timestamps(self):
		if not self.comments:
			self.comments = self.get_comments()
		timestamps = []
		for comment in self.comments.values:
			try:
				[timestamps.append(ts) for ts in split_timestamps(re.findall(PATTERN, comment))]
			except Exception as e:
				pass
		return timestamps

	def timestamps_timeintervals(self):
		if not self.timestamps:
			self.timestamps = self.get_timestamps()
		return [t for t in self.timestamps if type(t)!=list], [t for t in self.timestamps if type(t)==list]

	def plot(self,offset=0, normalized=False):
		if not self.dbs:
			self.dbs = self.get_dbs()
		time = np.linspace(offset,self.length+offset,self.num_chunks)
		max_dbs = np.amax(self.dbs) # min-max normalization
		min_dbs = np.amin(self.dbs)
		dbs = (self.dbs - min_dbs) / (max_dbs - min_dbs)
		plt.plot(time,dbs*20,c='w',linewidth=.5,alpha=.5)
		if not self.timeintervals:
			self.timestamps, self.timeintervals = self.timestamps_timeintervals()
		plt.hist([(t+offset) for t in self.timestamps],bins=np.arange(offset,self.length+offset,self.delta_t),color=self.plot_color)
		for i,interval in enumerate(self.timeintervals):
			plt.plot([(val+offset) for val in interval],[i]*len(interval),marker='o',c=self.plot_color,markersize=2,markeredgecolor='k',alpha=.8)

	def get_comments(self, max_pages=100):
		filename = os.path.join('comments',self.title+'.csv')
		if os.path.exists(filename):
			print('Loading comments from file')
			df = pd.read_csv(filename)['0']
			return df
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
		nextToken = response['nextPageToken']
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
				comments.append(c['snippet']['topLevelComment']['snippet']['textOriginal'])
			try:
				nextToken = response['nextPageToken']
			except:
				break
			print(f'Page {i}/{max_pages}', end='\r')
			i+=1
		comments = pd.Series(comments)
		comments.dropna(axis=0,inplace=True)
		comments.to_csv(filename)
		return comments

if __name__ == '__main__':
	yt = YoutubeVideo(url='https://www.youtube.com/watch?v=qJ5sic6pYbo&list=PL3tRBEVW0hiAl6bH2ywV_IabJvVqBM-vG&index=2')
	yt.set_plot_color([66/255.,135/255.,245/255.])
	yt.set_delta_t(10)
	print(yt.views)
	yt.plot(normalized=True)
	plt.gca().set_facecolor((.3,.3,.3))
	plt.show()