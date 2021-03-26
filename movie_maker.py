import subprocess
import os
import glob

transition_video = 'transition.mp4'
ending_video = 'ending.mp4'


def clean_text(title):
	# parsing on parsing on parsing on parsing
	return title.replace('\'','\\\\\\\\\\\'') # just a ridiculous function but it's correct haha

def create_video_clips(video, audio, time_intervals, output_file, overlay_text='', overwrite=False):
	if overwrite or not os.path.exists(output_file):
		# combine video and audio first
		command = f'ffmpeg -y -i "{video}" -i "{audio}" -c:v copy -c:a aac "./temp_output.mp4"'
		
		print(command)
		subprocess.call(command, shell=True)

		# cut video into a highlight reel
		num = len(time_intervals)
		if num==1:
			t = time_intervals[0]
			command = f'ffmpeg -y -i "./temp_output.mp4" -i "{transition_video}" -vsync 2 -filter_complex ' + \
					f'[1:v]setpts=PTS-STARTPTS,format=yuv420p[tv];[1:a]asetpts=PTS-STARTPTS[ta];' + \
					f'[0:v]trim=start={t[0]}:end={t[1]},setpts=PTS-STARTPTS,format=yuv420p[0v];[0:a]atrim=start={t[0]}:end={t[1]},asetpts=PTS-STARTPTS[0a];' + \
					f'[0v]drawtext=text="{clean_text(overlay_text)}":enable=\'between(t,0,5)\':x=60:y=60:fontsize=42:bordercolor="white":borderw=3:fontfile=Stanberry.ttf[0v_text] ' + \
					f'-map [0v_text] -map [0a] "{output_file}"'
		if num>1:
			command = f'ffmpeg -y -i "./temp_output.mp4" -i "{transition_video}" -vsync 2 -filter_complex ' + \
					f'[0:v]trim=start={time_intervals[0][0]}:end={time_intervals[0][1]},setpts=PTS-STARTPTS,format=yuv420p[0v];[0:a]atrim=start={time_intervals[0][0]}:end={time_intervals[0][1]},asetpts=PTS-STARTPTS[0a];' + \
					f'[0v]drawtext=text="{clean_text(overlay_text)}":enable=\'between(t,0,5)\':x=60:y=60:fontsize=42:bordercolor="white":borderw=3:fontfile=Stanberry.ttf[0v_text];' + \
					''.join([f'[0:v]trim=start={t[0]}:end={t[1]},setpts=PTS-STARTPTS,format=yuv420p[{i+1}v];[0:a]atrim=start={t[0]}:end={t[1]},asetpts=PTS-STARTPTS[{i+1}a];' for i, t in enumerate(time_intervals[1:])]) + \
					'[0v_text][0a][1:v][1:a]'+f'[1:v][1:a]'.join([f'[{i}v][{i}a]' for i in range(1,len(time_intervals))]) + \
					f'concat=n={len(time_intervals)*2-1}:v=1:a=1[outv][outa] -map [outv] -map [outa] "{output_file}"'
		if len(time_intervals)>0:
			print('-'*10)
			print(command)
			print('-'*10)
			subprocess.call(command, shell=True)
		os.remove('temp_output.mp4')

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


def combine_highlight_reels(clips_folder, output_file, delete_clips=False):
	search = sorted(glob.glob(os.path.join(clips_folder,'*.mp4')), key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
	command = f'ffmpeg -y -i {transition_video} ' + ' '.join([f'-i "{filename}"' for filename in search]) + ' -vsync 2 -filter_complex ' + \
			'[0:v][0:a]'.join([f'[{i+1}:v][{i+1}:a]' for i in range(len(search))]) + f'concat=n={len(search)*2-1}:v=1:a=1[outv][outa] -map [outv] -map [outa] "{output_file}"'
	print(command)
	subprocess.call(command, shell=True)
	if delete_clips:
		for file in glob.glob(os.path.join(clips_folder,'*.mp4')):
			os.remove(file)

def upload_video(file, title, description, category=20, keywords='gaming,compilation,compilations', privacyStatus='public'):
	command = f'python uploader.py --file "{file}" --title "{title}" --description "{description}" --category {category} --keywords "{keywords}" --privacyStatus "{privacyStatus}" --noauth_local_webserver'
	print(command)
	subprocess.call(command, shell=True)

if __name__ == '__main__':
	combine_highlight_reels('concatenated_output.mp4')
