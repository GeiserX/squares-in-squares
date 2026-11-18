"""Controls for seed attribution and the source-qualified round24 threshold."""
import csv
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import harvest_seeds as P
import harvest_follow as H

class SeedControls(unittest.TestCase):
    def test_named_seed_roots_and_idempotent_labels(self):
        origins={123:'couzo',504:'samanyu'}
        for source,flag,seeds in (
            ('our own grid construction','no',()),
            ('n = 504 of Samanyu-dev/squares_in_squares','yes',(504,)),
            ('504h.F2 <held: seed merged0>','yes',(504,)),
            ('123h.F1 <held: seed merged0>','no',()),
            ('seed merged0, see README','unknown',()),
            ('ours, on: see source','unknown',()),
            ('Ours, on: See Source','unknown',()),
            ('Exact donor unresolved packing; ours','unknown',()),
            ('copied record [Samanyu seed ancestry: unknown (seed root needs a record)]','unknown',())):
            row=dict(source=source,licence='ours')
            marked,actual,roots=P.annotate(row,source,origins)
            self.assertEqual((actual,roots),(flag,seeds))
            again,actual2,roots2=P.annotate(marked,source+' '+marked['licence'],origins)
            self.assertEqual(marked,again)
            self.assertEqual((actual2,roots2),(flag,seeds))

    def test_large_source_table_exceeds_the_old_reader_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.tsv'
            source='retained source notice '*8000
            path.write_text('n\tsource\n2\t'+source+'\n')
            configured=csv.field_size_limit()
            self.assertGreater(configured,len(source))
            try:
                csv.field_size_limit(131072)
                with self.assertRaises(csv.Error):H.table(path)
                csv.field_size_limit(configured)
                self.assertEqual(H.table(path)[0]['source'],source)
            finally:csv.field_size_limit(configured)

    def test_archived_parent_pointer_is_not_a_seed_free_root(self):
        with tempfile.TemporaryDirectory() as directory:
            s=Path(directory);t=s/'take-harvest-r24';ledger=s/'take-border-r23/take.tsv'
            ledger.parent.mkdir()
            ledger.write_text('n\tsource\tlicence\n735\tn=790 from held round21\tours\n')
            history=s/'history';history.mkdir()
            (history/'round19-best-2026-11-12.tsv').write_text('n\tsource\tlicence\n790\tn = 365 of Samanyu-dev/squares_in_squares\tno licence\n')
            policy=P.SeedPolicy(s,t,H.source_text,H.table,H.rows_write);policy.results=history
            row=dict(source='Exact donor '+str(ledger.parent/'735.csv'),licence='ours')
            marked,flag,roots=policy.mark(row)
            self.assertEqual((flag,roots),('yes',(365,)))
            self.assertIn('expanded recorded parents',marked['source'])
            missing=dict(source='Exact donor '+str(ledger.parent/'736.csv'),licence='ours')
            self.assertEqual(policy.mark(missing)[1],'unknown')

    def test_old_seed_result_cannot_shadow_a_clean_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            s=Path(directory);t=s/'take-harvest-r24';w=t/'work'
            (s/'gate/cand-round22-1113b').mkdir(parents=True)
            (s/'gate/cand-round22-1113b/details.csv').write_text('n,score\n503,0.03\n')
            w.mkdir(parents=True)
            rows=[dict(n=503,held='.02',new=score,gain='0',source=source,licence='ours',start=score,polish_gain='0')
                  for score,source in (('.019','n = 504 of Samanyu-dev/squares_in_squares'),('.025','our own grid construction'))]
            H.write_table(t/'take.tsv',rows)
            policy=P.SeedPolicy(s,t,H.source_text,H.table,H.rows_write)
            policy.clean_counts={503}
            policy.prepare=lambda collector: None
            collector=H.DeadlineCollector.__new__(H.DeadlineCollector)
            collector.args=SimpleNamespace(details=str(s/'gate/base/details.csv'),own=[],out=[str(t)])
            collector.work=w/'collector'
            collector.seed_policy=policy
            with patch.object(H.Collector,'run',lambda self:H.table(t/'take.tsv')):
                result=collector.run()
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['new'],'.025')
            self.assertIn('ancestry: no',result[0]['licence'])

    def test_clean_alternative_survives_a_stronger_seed_result(self):
        with tempfile.TemporaryDirectory() as directory:
            s=Path(directory);t=s/'take-harvest-r24';w=t/'work'
            (s/'gate/cand-round22-1113b').mkdir(parents=True)
            (s/'gate/cand-round22-1113b/details.csv').write_text('n,score\n503,0.03\n')
            for folder,score,source in [('candidates',.019,'n = 504 of Samanyu-dev/squares_in_squares'),('clean-candidates',.025,'our own grid construction')]:
                path=w/folder;path.mkdir(parents=True)
                H.rows_write(path/'503.csv',[dict(n=503,square_id=0,x='.5',y='.5',angle='0')])
                H.write_table(path/'take.tsv',[dict(n=503,held=.02,new=score,gain=.02-score,source=source,licence='ours',start=score,polish_gain=0)])
            policy=P.SeedPolicy(s,t,H.source_text,H.table,H.rows_write)
            collector=SimpleNamespace(strict_held={503:.02},args=SimpleNamespace(own=[]))
            policy.prepare(collector)
            chosen=H.table(w/'policy-candidates/take.tsv')[0]
            self.assertEqual(float(chosen['new']),.025)
            self.assertEqual(collector.held[503],.03)
            self.assertIn('ancestry: no',chosen['licence'])
            self.assertFalse(policy.peer_allowed(dict(n=503,source='n = 504 of Samanyu-dev/squares_in_squares',licence='ours')))
            self.assertTrue(policy.peer_allowed(dict(n=503,source='our own grid construction',licence='ours')))
            # A clean alternative above the allowed held score must not win.
            rows=H.table(w/'clean-candidates/take.tsv');rows[0]['new']='.031';H.write_table(w/'clean-candidates/take.tsv',rows)
            policy.prepare(collector)
            chosen=H.table(w/'policy-candidates/take.tsv')[0]
            self.assertEqual(float(chosen['new']),.019)
            self.assertEqual(collector.held[503],.02)
            self.assertIn('seed n=504',chosen['licence'])

if __name__=='__main__':unittest.main()
