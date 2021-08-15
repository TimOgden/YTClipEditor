import subprocess
import os
import glob

transition_video = '"./videos/transition.mp4"'
ending_video = '"./videos/ending.mp4"'


def clean_text(title):
	# parsing on parsing on parsing on parsing
	return title.replace('\'','\\\\\\\\\\\'') # just a ridiculous function but it's correct haha

def create_video_clips(video, audio, time_intervals, output_file, overlay_text='', overwrite=False, delete_clips=True):
	if overwrite or not os.path.exists(output_file):
		# combine video and audio first
		command = f'ffmpeg -y -i "{video}" -i "{audio}" -c:v copy -c:a aac "./videos/temp_output.mp4"'
		
		print(command)
		subprocess.call(command, shell=True)

		# cut video into a highlight reel
		for i,t in enumerate(time_intervals):
			if i == 0:
				command = f'ffmpeg -y -vsync 0 -hwaccel cuda -hwaccel_output_format cuda -ss {t[0]} -i "./videos/temp_output.mp4" -to {t[1]}' + \
							f' -vf "drawtext=text=\'{clean_text(overlay_text)}\':enable=\'between(t,0,5)\':x=60:y=60:fontsize=42:bordercolor=\'white\':borderw=3:fontfile=Stanberry.tff"' + \
							f' -c:a copy -c:v h264_nvenc -b:v 5M "./videos/clips/{i}.mp4"'
				print(command)
				subprocess.call(command, shell=True)
			else:
				command = f'ffmpeg -y -vsync 0 -hwaccel cuda -hwaccel_output_format cuda -ss {t[0]} -i "./videos/temp_output.mp4" -to {t[1]}' + \
							f' -c:a copy -c:v h264_nvenc -b:v 5M "./videos/clips/{i}.mp4"'
				subprocess.call(command, shell=True)
		with open('concat_list.txt', 'w') as f:
			f.write(f'\n{transition_video}'.join(glob.glob('videos/clips/*.mp4')))
			f.write(ending_video)
		command = 'ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy "./videos/concatenated_output.mp4"'
		os.remove('./videos/temp_output.mp4')
		if delete_clips:
			[os.remove(file) for file in glob.glob('videos/clips/*.mp4')]

def clean_folder(playlist, folder, retry=False):
	# check if any videos are 0 bytes and try again
	for file in glob.glob(os.path.join(folder,'*.mp4')):
		bytes_num = os.stat(file).st_size
		if bytes_num==0:
			if retry:
				# video didn't render, try again
				index_ = int(os.path.splitext(os.path.basename(file))[0])
				yt = playlist.videos[index_]
				create_video_clips(yt.video_path,yt.audio_path,yt.gti,f'./clips/{index_}.mp4',overlay_text=yt.original_title)
			else:
				os.remove(file)

def upload_video(file, title, description, category=20, keywords='gaming,compilation,compilations', privacyStatus='public'):
	command = f'python uploader.py --file "{file}" --title "{title}" --description "{description}" --category {category} --keywords "{keywords}" --privacyStatus "{privacyStatus}" --noauth_local_webserver'
	print(command)
	subprocess.call(command, shell=True)

if __name__ == '__main__':
	combine_highlight_reels('concatenated_output.mp4')
