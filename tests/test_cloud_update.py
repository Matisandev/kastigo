import copy, datetime, pathlib, sys, unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import cloud_update as c
BASE=(c.ROOT/'index.html').read_bytes()
URL='https://www.enap.cl/informe-semanal-de-precios'
# Source already in the original page is used for successful fixtures.
URL=c.blocks(BASE)[1]['data']['news'][0]['sources'][0]['u']
class Validation(unittest.TestCase):
 def proposal(self,path='/lede',value='Resumen verificado.'):
  return {'changes':[{'path':path,'es':value,'en':value,'pt':value,'sources':[URL]}]}
 def test_shell_unchanged(self):
  new=c.candidate(BASE,self.proposal(),{URL},'2026-11-12T09:00:00-03:00')
  self.assertEqual(c.blocks(BASE)[0],c.blocks(new)[0])
 def test_no_news(self):self.assertIsNone(c.candidate(BASE,{'changes':[]},set(),'unused'))
 def test_fixed_fields(self):
  for p in ['/editorial','/stance','/stanceName','/updated']:
   with self.assertRaises(ValueError):c.candidate(BASE,self.proposal(p),{URL},'unused')
 def test_unopened_source(self):
  with self.assertRaises(ValueError):c.candidate(BASE,self.proposal(),set(),'unused')
 def test_missing_field(self):
  with self.assertRaises(ValueError):c.candidate(BASE,self.proposal('/made_up'),{URL},'unused')
 def test_missing_sections(self):
  with self.assertRaises(ValueError):c.candidate(BASE,self.proposal('/news',[]),{URL},'unused')
 def test_numeric_translation(self):
  old=c.blocks(BASE)[1]['data']
  def find(x,path=''):
   if isinstance(x,dict):
    for k,v in x.items():
     r=find(v,path+'/'+k)
     if r:return r
   elif isinstance(x,list):
    for k,v in enumerate(x):
     r=find(v,path+'/'+str(k))
     if r:return r
   elif type(x) in [int,float]:return path,x
  p,v=find(old);proposal=self.proposal(p,v);proposal['changes'][0]['en']=v+1
  with self.assertRaises(ValueError):c.candidate(BASE,proposal,{URL},'unused')
 def test_markup(self):
  with self.assertRaises(ValueError):c.candidate(BASE,self.proposal(value='<script>alert(1)</script>'),{URL},'unused')
 def test_search_is_not_opened(self):
  r={'output':[{'type':'web_search_call','action':{'type':'search','sources':[{'url':URL}]}}]}
  self.assertEqual(c.opened_urls(r),set())
 def test_incomplete_response(self):
  with self.assertRaises(ValueError):c.response_text({'status':'incomplete'})
 @patch.object(c,'gh')
 def test_existing_day_skips(self,gh):
  gh.return_value={'object':{'sha':'abc'}};self.assertFalse(c.claim_day('2026-11-12','abc'));self.assertEqual(gh.call_count,1)
 @patch.object(c,'gh')
 def test_claim_atomic(self,gh):
  gh.side_effect=[RuntimeError('Solicitud rechazada: HTTP 404'),{}]
  self.assertTrue(c.claim_day('2026-11-12','abc'))
  self.assertEqual(gh.call_args.args[1],'POST')
 def test_day_uses_santiago(self):
  t=datetime.datetime(2026,11,13,1,tzinfo=datetime.timezone.utc)
  self.assertEqual(t.astimezone(c.ZONE).date().isoformat(),'2026-11-12')
if __name__=='__main__':unittest.main()
