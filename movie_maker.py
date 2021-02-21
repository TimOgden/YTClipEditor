import subprocess

def clip_video(video, audio, time_intervals, output_file, overlay_text=None):
	#command = 'ffmpeg -i "{}" -i "{}" -c:v copy -c:a aac "{}"'.format(video, audio, output_file)
	if overlay_text:
		overlay_text = overlay_text.replace(':','').replace('"','').replace('\'','')
		command = f'ffmpeg -y -i "{video}" -i "{audio}"  -vf "select=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
					+ f'\', setpts=N/FRAME_RATE/TB, drawtext=fontfile=Stanberry.tiff:enable=\'between(t,0,3)\':text=\'{overlay_text}\':x=50:y=50:fontsize=50:borderw=2:bordercolor=black:fontcolor=white" ' \
					+ f'-af "aselect=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
					+ f'\',asetpts=N/SR/TB" "{output_file}"'
	else:
		command = f'ffmpeg -y -i "{video}" -i "{audio}"  -vf "select=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
					+ f'\', setpts=N/FRAME_RATE/TB"' \
					+ f'-af "aselect=\'' + '+'.join([f'between(t,{t[0]},{t[1]})' for t in time_intervals]) \
					+ f'\',asetpts=N/SR/TB" "{output_file}"'
	print(command)
	subprocess.call(command, shell=True)