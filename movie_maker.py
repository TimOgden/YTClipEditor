import subprocess
import os
import glob

transition_video = 'transition.mp4'
ending_video = 'ending.mp4'
output_video = 'output_w_transitions.mp4'
def clip_video(video, audio, time_intervals, output_file, overlay_text=''):
	overlay_text = overlay_text.replace(':','').replace('"','').replace('\'','')
	command = f'ffmpeg -y -i "{video}" -i "{audio}"  -vf "select=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
				+ f'\', setpts=N/FRAME_RATE/TB, drawtext=fontfile=Stanberry.tiff:enable=\'between(t,0,3)\':text=\'{overlay_text}\':x=50:y=50:fontsize=50:borderw=2:bordercolor=black:fontcolor=white" ' \
				+ f'-af "aselect=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
				+ f'\',asetpts=N/SR/TB" "{output_file}"'
	subprocess.call(command, shell=True)

def create_video_clips(video, audio, time_intervals, output_file, overlay_text=''):
	overlay_text = overlay_text.replace(':','').replace('"','').replace('\'','')
	# combine video and audio first
	command = f'ffmpeg -y -i "{video}" -i "{audio}" -c:v copy -c:a aac "./temp_output.mp4"'
	subprocess.call(command, shell=True)

	# cut video into a highlight reel
	num = len(time_intervals)
	command = f'ffmpeg -y -i "./temp_output.mp4" -i "{transition_video}" -vsync 2 -filter_complex ' + \
			''.join([f'[0:v]trim=start={t[0]}:end={t[1]},setpts=PTS-STARTPTS,format=yuv420p[{i}v];[0:a]atrim=start={t[0]}:end={t[1]},asetpts=PTS-STARTPTS[{i}a];' for i, t in enumerate(time_intervals)]) + \
			f'[1:v][1:a]'.join([f'[{i}v][{i}a]' for i in range(len(time_intervals))]) + \
			f'concat=n={len(time_intervals)*2-1}:v=1:a=1[outv][outa] -map [outv] -map [outa] "{output_file}"' 
	if len(time_intervals)>0:
		print('-'*10)
		print(command)
		print('-'*10)
		subprocess.call(command, shell=True)

def write_script_file(playlist, script_file_loc='script.txt', transition_video=None, end_video=None, delete_after=False):
	filepath = os.path.join('clips/',playlist)
	dirs = os.listdir(filepath)
	with open(script_file_loc,'w') as f:
		for i,directory_name in enumerate(dirs):
			print('Directory name:',directory_name)
			search = os.path.join(filepath,directory_name) + '/*.mp4'
			glob_search = glob.glob(search)
			if len(glob_search)>0:
				for file in glob_search:
					if transition_video:
						f.write(f"file \'{transition_video}\'\n")
					f.write(f'file \'{file}\'\n')
		if end_video:
			f.write(f'file \'{end_video}\'')
	return script_file_loc

def combine_script_file(output_file, script_file):
	command = f'ffmpeg -f concat -y -safe 0 -i "{script_file}" "{output_file}"'
	print(command)
	subprocess.call(command, shell=True)



if __name__=='__main__':
	script = write_script_file('Wind Waker - Game Grumps', transition_video='transition.mp4', end_video='ending.mp4')
	combine_script_file('output_w_transitions.mp4', script)
