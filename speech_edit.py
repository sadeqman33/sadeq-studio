"""Read-only speech take suggestions from cached, source-timed ASR evidence.

These are editing hypotheses, not a speech-error detector or acoustic assessment.
The calling agent chooses coherent takes; this module never deletes or edits audio.
"""
import difflib, math, re, unicodedata

VERSION='speech-picks-1'
RULES='''Speech-first editing: compare complete source takes against the requested idea. Cached speech picks are hypotheses from automatic ASR, not verified speaker errors or acoustic quality. Prefer a coherent complete take over a false start only when the meaning is the same. Check surrounding transcript context and source audio for ambiguous choices. Preserve negation, qualifiers, names, prices and numbers; a correction may change a fact, so never choose a fact by fluency alone. Do not remove all pauses, dialect words or deliberate emphasis. Use only real source-time ranges, leave small breathing margins and avoid clipping word beginnings/endings. Never fabricate words or assemble isolated syllables into speech the speaker did not say. Explain which repeated takes were kept and why in the plan reason. If ASR missed a stumble or timestamps are unreliable, request/mark listening review, not a claim of perfect cleanup. Original sources stay intact and every cut remains editable.'''
FILLERS={'ام','مم','اا','ااا','ااه','اه','اااا'}
NEGATIONS={'لا','مو','مش','ما','ماكو','ليس','ليست','بدون','غير','لم','لن'}
CORRECTIONS=re.compile(r'(?:خليني\s+(?:اعيد|أعيد)|ن(?:عيد|رجع)\s+من\s+(?:البداية|جديد)|اقصد|أقصد|قصدي|غلطت|عفوا)')

def tokens(text):
    text=unicodedata.normalize('NFKC',text).casefold()
    text=re.sub(r'[\u064b-\u065f\u0670\u0640]','',text)
    text=text.translate(str.maketrans('أإآى','اااي'))
    return re.findall(r'[\w]+',text)

def finite(value):
    try:
        value=float(value)
        return value if math.isfinite(value) else None
    except (TypeError,ValueError):return None

def critical(text):
    ts=tokens(text)
    # Keep digit spelling normalized, but do not guess spoken-number equivalence.
    number_text=''.join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    numbers=re.findall(r'\d+(?:[.,]\d+)*',number_text)
    number_words={'واحد','اثنين','ثلاثة','اربعة','خمسة','ستة','سبعة','ثمانية','تسعة','عشرة','عشرين','ثلاثين','اربعين','خمسين','ستين','سبعين','ثمانين','تسعين','مية','مئة','الف','مليون','عشر','عشره','عشرة','وخمسة','وعشرين'}
    return ([x for x in ts if x in NEGATIONS], numbers, [x for x in ts if x in number_words])

def units(seg):
    """Use word boundaries only when they faithfully cover the accepted transcript."""
    a,b=finite(seg.get('start')),finite(seg.get('end'))
    if a is None or b is None or a<0 or b<=a or not str(seg.get('text','')).strip():return []
    words=[]
    for w in seg.get('words',[]):
        x,y=finite(w.get('start')),finite(w.get('end'));text=str(w.get('text','')).strip()
        if x is None or y is None or not text or not a<=x<y<=b+.001 or (words and x<words[-1]['end']-.03):
            return [{'start':a,'end':b,'text':seg['text'],'words':[],'boundary':'segment'}]
        words.append({**w,'start':x,'end':y,'text':text})
    if not words or tokens(' '.join(w['text'] for w in words))!=tokens(seg['text']):
        return [{'start':a,'end':b,'text':seg['text'],'words':[],'boundary':'segment'}]
    parts=[];current=[]
    for w in words:
        if current and (w['start']-current[-1]['end']>=.65 or re.search(r'[.!؟?؛]$',current[-1]['text'])):
            parts.append(current);current=[]
        current.append(w)
    if current:parts.append(current)
    return [{'start':ws[0]['start'],'end':ws[-1]['end'],'text':' '.join(w['text'] for w in ws),'words':ws,'boundary':'words'} for ws in parts]

def picks(transcript):
    result={'version':VERSION,'status':'unavailable','automatic':True,'audio_listened':False,
            'note':'اقتراحات من تفريغ آلي؛ مو إثبات إنك غلطت. اسمع المحاولة قبل اعتماد القص.',
            'candidates':[],'retake_groups':[],'uncertain_ranges':[],
            'rules':RULES}
    if not transcript:return result
    result['status']=transcript.get('status','unavailable')
    # Partial and no-speech output never become a usable speech-edit plan.
    if result['status']!='transcribed':return result
    result['uncertain_ranges']=[{'start':s.get('start'),'end':s.get('end'),'text':s.get('text',''),'reason':s.get('reason','تفريغ غير مؤكد')} for s in transcript.get('uncertain',[])]
    segments=sorted(transcript.get('segments',[]),key=lambda s:finite(s.get('start')) or 0)
    for si,seg in enumerate(segments):
        for unit in units(seg):
            ts=tokens(unit['text']);reasons=[];penalty=0
            repeated=[]
            for n in range(1,min(6,len(ts)//2)+1):
                for i in range(len(ts)-2*n+1):
                    if ts[i:i+n]==ts[i+n:i+2*n]:repeated.append(' '.join(ts[i:i+n]))
            if repeated:reasons.append('تكرار متجاور محتمل؛ ممكن يكون تأكيد مقصود');penalty+=2
            if any(x in FILLERS for x in ts):reasons.append('تردد لفظي محتمل');penalty+=1
            if CORRECTIONS.search(unit['text']):reasons.append('إشارة إعادة أو تصحيح؛ راجع المعنى قبل القص');penalty+=2
            if unit['text'].rstrip().endswith(('…','...','-')):reasons.append('نهاية متروكة محتملة');penalty+=2
            if len(ts)<3:reasons.append('عبارة قصيرة؛ تحتاج سياق');penalty+=1
            quality=seg.get('asr_quality',{});logprob=finite(quality.get('avg_logprob'))
            # ASR confidence is a secondary tie-breaker, never vocal performance.
            score=round(10-penalty+(max(-1,min(0,logprob)) if logprob is not None else 0),3)
            result['candidates'].append({'id':f's{si+1}u{len(result["candidates"])+1}',
                'segment_index':si,'start':round(unit['start'],3),'end':round(unit['end'],3),
                'text':unit['text'],'boundary':unit['boundary'],'word_times':unit['words'],
                'signals':reasons,'relative_score':score,'asr_quality':quality,
                'needs_review':True,'listen_start':round(max(0,unit['start']-.3),3),
                'listen_end':round(unit['end']+.3,3)})
    # Nearby look-alike utterances are retake hypotheses, not automatic removals.
    candidates=result['candidates'];groups=[]
    for i,c in enumerate(candidates):
        ct=tokens(c['text']);ct=[t for t in ct if t not in FILLERS]
        if len(ct)<3:continue
        for prev in candidates[max(0,i-12):i]:
            if c['start']-prev['end']>90:continue
            pt=[t for t in tokens(prev['text']) if t not in FILLERS]
            if len(pt)<3:continue
            same=ct==pt;prefix=ct[:len(pt)]==pt or pt[:len(ct)]==ct
            ratio=difflib.SequenceMatcher(a=ct,b=pt,autojunk=False).ratio()
            if not same and not (prefix or ratio>=.82):continue
            g=next((g for g in groups if prev['id'] in g),None)
            if g is None:g=[prev['id']];groups.append(g)
            if c['id'] not in g:g.append(c['id'])
            break
    lookup={c['id']:c for c in candidates}
    for i,ids in enumerate(groups):
        cs=[lookup[k] for k in ids];ordered=sorted(cs,key=lambda c:(-c['relative_score'],c['start']))
        signatures={str(critical(c['text'])) for c in cs};contents={tuple(t for t in tokens(c['text']) if t not in FILLERS) for c in cs}
        safe=len(signatures)==1 and len(contents)==1
        preferred=ordered[0]['id'] if safe and ordered[0]['relative_score']>ordered[-1]['relative_score'] else None
        result['retake_groups'].append({'id':f'r{i+1}','candidate_ids':ids,
            'ranked_candidate_ids':[c['id'] for c in ordered],'preferred_candidate':preferred,
            'meaning_review_required':not safe,
            'note':'احتمال إعادة جملة. '+('المعنى أو رقم/نفي مختلف؛ الإيجنت يراجع السياق، ما يختار بالترتيب وحده.' if not safe else 'الكلمات متطابقة تقريباً؛ ترتيب مبدئي حسب التردد المكتوب، يحتاج سماع.')})
    return result
