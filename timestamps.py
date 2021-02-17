

def split_timestamps(timestamps):
    arr = []
    for ts in timestamps:
        ts = ts.split('-')
        if len(ts)==1:
            arr.append(convert_timestamp(ts[0]))
        else:
            val = []
            for t in ts:
                val.append(convert_timestamp(t))
            arr.append(val)
    return arr

def convert_timestamp(ts, debug=False):
    ts = ts.replace(' ', '')
    ts = ts.split(':')
    
    seconds = 0
    for i,t in enumerate(ts[::-1]):
        #print(i,t)
        seconds += int(t)*(60**i)
        if debug:
            print(f'seconds+={t}*(60^{i})={int(t)*(60**i)}')
    if debug: print('--')
    return seconds