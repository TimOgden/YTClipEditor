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

def overlap(t0,t1):
    if t0 and not t1:
        return 0
    if t1 and not t0:
        return 0
    if not t0 and not t1:
        return 0
    if t0[0]<t1[0]:
        # t0 starts first
        if t0[1] > t1[0]:
            return t0[1] - t1[0]
        else:
            return 0
    else:
        # t1 starts first
        if t1[1] > t0[0]:
            return t0[0] - t1[1]
        else:
            return 0

def merge(t0,t1):
    if t0[0]<t1[0]:
        # t0 starts first
        return [t0[0],t1[1]]
    else:
        # t1 starts first
        return [t1[0],t0[1]]