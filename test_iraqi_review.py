import copy,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import iraqi_review as iq
import server
class IraqiReviewTests(unittest.TestCase):
    def fixture(self):
        p={'assets':[],'timeline':[],'profile':{'brand':'Academy'},'ratio':'9:16','exports':[{'version':'v1','duration':12}], 'market':iq.market({'segment':'أصحاب متاجر عراقيين','account':'@academy','objective':'sales','distribution':'paid'})}
        d={'export_version':'v1','post_key':'post1','published_at':(datetime.now(ZoneInfo('Asia/Baghdad'))-timedelta(days=3)).isoformat(),'window_hours':24,'views':1000,'shares':50,'orders':10,'spend_iqd':20000,'revenue_iqd':150000}
        return p,d
    def test_reported_metrics_and_zero_vs_unknown(self):
        p,d=self.fixture();r=iq.outcome(d,p)
        self.assertEqual(r['metrics']['shares_per_1000_views'],50);self.assertEqual(r['metrics']['cost_per_orders_iqd'],2000);self.assertEqual(r['metrics']['roas'],7.5)
        self.assertIsNone(r['likes']);self.assertIsNone(r['metrics']['likes_per_1000_views'])
        d['orders']=0;r=iq.outcome(d,p);self.assertEqual(r['metrics']['orders_per_1000_views'],0);self.assertIsNone(r['metrics']['cost_per_orders_iqd'])
        d['views']=0;r=iq.outcome(d,p);self.assertIsNone(r['metrics']['shares_per_1000_views']);self.assertNotEqual(iq.outcome(d,p)['id'],iq.outcome(d,p)['id'])
    def test_invalid_age_exports_infinite_metrics(self):
        p,d=self.fixture()
        for field,val in [('views',-1),('views',1.1),('completion_pct',101),('orders',float('nan')),('spend_iqd',float('inf')),('window_hours',100000),('export_version','other-project')]:
            with self.subTest(field=field,val=val),self.assertRaises(ValueError):iq.outcome({**d,field:val},p)
        with self.assertRaises(ValueError):iq.outcome({**d,'market':iq.market({'distribution':'organic'})},p)
    def test_cohorts_do_not_mix_platform_paid_goal_age_segment_or_account(self):
        p,d=self.fixture();base=iq.outcome(d,p);records=[base]
        for field,value in [('platform','tiktok'),('distribution','organic'),('objective','awareness'),('segment','طلاب'),('location','البصرة'),('account','@second')]:
            other=copy.deepcopy(base);other['post_key']=field;other['market'][field]=value;other['metrics']['orders_per_1000_views']=500;records.append(other)
        other=copy.deepcopy(base);other['window_hours']=48;other['metrics']['orders_per_1000_views']=100;records.append(other)
        c=iq.comparison(records,p['market']);self.assertEqual([(x['window_hours'],x['median'],x['n_posts']) for x in c],[(24,10,1),(48,100,1)])
        self.assertEqual(iq.comparison(records,{**p['market'],'segment':''}),[]);self.assertEqual(iq.comparison(records,{**p['market'],'account':''}),[])
        self.assertEqual(c[0]['status'],'descriptive_only');self.assertIsNone(c[0]['probability'])
    def test_evidence_gating_audio_and_insufficient_coverage(self):
        raw={'summary':'review','criteria':{k:{'score':5,'reason':'good','evidence':['frame-00']} for k in iq.CRITERIA},'fixes':[{'time':1,'change':'change','why':'why'}],'hook_variants':['one'],'missing':[]}
        r=iq.finalize(raw,[{'id':'frame-00'}],12,'fingerprint');self.assertEqual(r['coverage'],80);self.assertIsNone(r['criteria']['audio']['score']);self.assertIsNone(r['criteria']['iraqi_fit']['score']);self.assertFalse(r['calibrated']);self.assertIsNone(r['probability'])
        for k in raw['criteria']:raw['criteria'][k]['evidence']=['invented']
        raw['criteria']['hook']['evidence']=['frame-00'];r=iq.finalize(raw,[{'id':'frame-00'}],12,'fingerprint');self.assertEqual(r['coverage'],25);self.assertIsNone(r['score'])
        raw['criteria']['hook']['score']=6
        with self.assertRaises(ValueError):iq.finalize(raw,[{'id':'frame-00'}],12,'fingerprint')
    def test_fingerprint_tracks_source_edit_and_audience_but_not_results(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'clip';f.write_bytes(b'old');p,_=self.fixture();p['assets']=[{'id':'a','path':str(f)}];p['timeline']=[{'asset':'a','start':0,'end':1,'text':'hi'}]
            fp=iq.fingerprint(p);p['results']=[{'views':10}];self.assertEqual(iq.fingerprint(p),fp)
            f.write_bytes(b'changed');self.assertNotEqual(iq.fingerprint(p),fp)
            fp=iq.fingerprint(p);p['market']['segment']='جمهور ثاني';self.assertNotEqual(iq.fingerprint(p),fp)
            fp=iq.fingerprint(p);p['timeline'][0]['start']=.1;self.assertNotEqual(iq.fingerprint(p),fp)
    def test_temporal_samples_match_export_and_originals_are_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            old=server.DATA;root=Path(t);server.DATA=root/'data';source=root/'source';source.mkdir()
            try:
                video=source/'clip.mp4';server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=320x240:r=30:d=2','-c:v','libx264','-y',str(video)])
                original=video.read_bytes();p=server.create('test',str(source));p['timeline']=[{'id':'c','asset':p['assets'][0]['id'],'start':0,'end':1.5,'text':'','mute':True,'textY':63}];server.save(p);server.export(p['id'],{})
                p=server.project(p['id']);rid,fp,dur,images,evidence,exported=server.review_context(p,{})
                self.assertIsNotNone(exported);self.assertGreaterEqual(len(images),4);self.assertTrue(all(0<=e['t']<dur for e in evidence if 't' in e));self.assertTrue(all(e['mode']=='rendered_export' for e in evidence if 'mode' in e));self.assertEqual(video.read_bytes(),original)
                p['timeline'][0]['text']='new';*_,exported=server.review_context(p,{});self.assertIsNone(exported)
            finally:server.DATA=old
if __name__=='__main__':unittest.main()
