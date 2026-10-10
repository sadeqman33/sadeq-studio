import copy, json, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import server, workflow, video_library as vl, speech_edit as se
from speech_worker import clean_segments

def transcript(*texts):
    return {'status':'transcribed','segments':[{'start':i*5+1,'end':i*5+4,'text':t,'words':[]} for i,t in enumerate(texts)],'uncertain':[]}

class SpeechPickTests(unittest.TestCase):
    def test_clearer_identical_take_is_only_a_reviewable_suggestion(self):
        t=transcript('آآآ حجز المزرعة صار أسهل','حجز المزرعة صار أسهل');before=copy.deepcopy(t)
        p=se.picks(t);group=p['retake_groups'][0]
        self.assertEqual(group['preferred_candidate'],p['candidates'][1]['id'])
        self.assertFalse(group['meaning_review_required']);self.assertFalse(p['audio_listened'])
        self.assertTrue(all(c['needs_review'] for c in p['candidates']))
        self.assertEqual(t,before);self.assertEqual(p['candidates'][1]['start'],6)

    def test_prices_negation_and_named_facts_are_not_chosen_by_fluency(self):
        for first,last in [('السعر هو ٢٠ دينار للحجز اليوم','السعر هو ٣٠ دينار للحجز اليوم'),
                           ('هذا النظام مجاني بالكامل','هذا النظام مو مجاني بالكامل'),
                           ('هذا العرض خاص بمدينة بغداد اليوم','هذا العرض خاص بمدينة البصرة اليوم')]:
            with self.subTest(first=first):
                p=se.picks(transcript(first,last));self.assertEqual(len(p['retake_groups']),1)
                self.assertTrue(p['retake_groups'][0]['meaning_review_required'])
                self.assertIsNone(p['retake_groups'][0]['preferred_candidate'])

    def test_unfinished_repetition_and_correction_are_hypotheses(self):
        p=se.picks(transcript('هذا هذا نظام للحجز…','خليني أعيد الجملة من البداية','هذا نظام للحجز يسهّل الشغل'))
        self.assertTrue(any('تكرار' in s for s in p['candidates'][0]['signals']))
        self.assertTrue(any('متروكة' in s for s in p['candidates'][0]['signals']))
        self.assertTrue(any('تصحيح' in s for s in p['candidates'][1]['signals']))
        self.assertEqual(len(p['candidates']),3)  # No automatic destructive cleanup.
        for status in ['partial','no_audio','speech_uncertain','no_speech_detected']:
            self.assertEqual(se.picks({**transcript('هلوسة فوق الموسيقى'), 'status':status})['candidates'],[])

    def test_word_boundaries_require_matching_monotonic_source_times(self):
        words=[{'text':t,'start':s,'end':s+.2} for t,s in [('هذا',1),('نظام',1.25),('للحجز.',1.5),('وهذا',3),('حجز',3.25),('جديد',3.5)]]
        t={'status':'transcribed','segments':[{'start':1,'end':4,'text':'هذا نظام للحجز. وهذا حجز جديد','words':words}]}
        p=se.picks(t);self.assertEqual([(c['start'],c['end']) for c in p['candidates']],[(1,1.7),(3,3.7)])
        for bad in [{'text':'جملة مخترعة','start':1,'end':1.2},{'text':'هذا','start':10,'end':11}]:
            tt=copy.deepcopy(t);tt['segments'][0]['words'][0]=bad
            c=se.picks(tt)['candidates'];self.assertEqual(len(c),1);self.assertEqual(c[0]['boundary'],'segment')
            self.assertEqual(c[0]['text'],t['segments'][0]['text'])

    def test_future_asr_metrics_keep_source_offsets_without_claiming_truth(self):
        raw=[{'start':1,'end':2,'text':'مرحبا','avg_logprob':-.2,'no_speech_prob':.01,'compression_ratio':1,
              'words':[{'start':1,'end':2,'word':'مرحبا','probability':.9}]}]
        good,bad=clean_segments(raw,20,30,[(21,22)])
        self.assertEqual(good[0]['asr_quality']['avg_logprob'],-.2)
        self.assertEqual(good[0]['words'][0]['asr_probability'],.9)
        self.assertEqual(good[0]['words'][0]['start'],21);self.assertTrue(good[0]['needs_review'])

    def test_context_uses_cached_speech_and_suppresses_changed_source(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);old=server.DATA;server.DATA=root/'data';src=root/'source';src.mkdir();video=src/'clip.mp4';video.write_bytes(b'fixture')
            http=ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                p=server.create('اختبار الكلام',str(src));a=p['assets'][0];p['analysis_at']=1
                p['video_analyses']={a['id']:{'asset':a['id'],'status':'complete','fingerprint':vl.fingerprint(a),'transcript':transcript('آآآ حجز المزرعة صار أسهل','حجز المزرعة صار أسهل')}};server.save(p)
                original=(server.DATA/p['id']/'project.json').read_bytes();client=workflow.StudioClient('http://127.0.0.1:'+str(http.server_port))
                with patch.object(vl,'transcribe',side_effect=AssertionError('No repeated ASR')),patch.object(server,'ask_agent',side_effect=AssertionError('No nested agent')):
                    ctx=client.context(p['id'],[a['id']])
                self.assertEqual(len(ctx['evidence'][0]['speech_picks']['retake_groups']),1)
                self.assertEqual((server.DATA/p['id']/'project.json').read_bytes(),original)
                video.write_bytes(b'changed fixture');ctx=client.context(p['id'],[a['id']])
                self.assertTrue(ctx['evidence'][0]['stale']);self.assertEqual(ctx['evidence'][0]['speech_picks']['candidates'],[])
            finally:http.shutdown();http.server_close();thread.join();server.DATA=old

if __name__=='__main__':unittest.main()
