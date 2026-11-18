#!/usr/bin/env python3
"""Controls for source ancestry, public credits and winning input discovery."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harvest_follow as H


class FollowControls(unittest.TestCase):
    def test_deadline_cleanup_checks_the_exact_command(self):
        script = Path('/scratch/harvest/public.sh')
        self.assertTrue(H.owned_public_fetch('bash ' + str(script), script))
        self.assertTrue(H.owned_public_fetch('/bin/bash ' + str(script), script))
        for command in ('cat ' + str(script), 'bash ' + str(script) + '.other',
                        'bash ' + str(script) + ' --extra', "python -c 'unterminated"):
            self.assertFalse(H.owned_public_fetch(command, script))

    def test_policy_text_is_not_ancestry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frozen = root / 'take-harvest-r22'
            frozen.mkdir()
            proof = 'a' * 64
            (frozen / 'take.tsv').write_text('n\tremote_quench\n639\tremote-' + proof + '.json\n')
            metadata = root / 'source.json'
            metadata.write_text(json.dumps(dict(source='approved n800 build', licence='ours, on Apache 2.0',
                policy=dict(excluded=['CC BY-SA 4.0', proof]))))
            row = dict(source='approved build (source metadata ' + str(metadata) + ')', licence='ours')
            self.assertIsNone(H.refused_source(row, root))
            metadata.write_text(json.dumps(dict(parts=dict(A=dict(source_record='parent remote-' + proof + '.json')))))
            self.assertIsNotNone(H.refused_source(row, root))
            metadata.write_text(json.dumps(dict(parts=dict(A=dict(licence='CC BY-SA 4.0')))))
            self.assertIsNotNone(H.refused_source(row, root))
            self.assertIsNotNone(H.refused_source(dict(source='held n = 801', licence='ours'), root))

    def test_carried_public_credits_and_missing_upstream(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root/'new'
            old = root/'old'
            owner = current/'nb/owner__book'
            parent = current/'nb/parent__book'
            previous = old/'nb/parent__book'
            for folder in (owner, parent, previous):
                folder.mkdir(parents=True)
            (parent/'meta.json').write_text(json.dumps(dict(carried=str(old))))
            (previous/'per_n.csv').write_text('n,L,source\n542,23.8,own local construction\n')
            credit = owner/'per_n.csv'
            credit.write_text('n,L,source_ref\n542,23.8,parent/book\n')
            row = dict(n='542', L='23.8', source='owner/book :: submission.csv', licence='Apache 2.0')
            good = H.public_origin(current, row)
            self.assertIn(str(previous/'per_n.csv'), good['source'])
            self.assertIsNone(H.refused_source(good, root))
            credit.write_text('n,L,source_ref\n542,23.8,missing/book\n')
            self.assertIsNotNone(H.refused_source(H.public_origin(current, row), root))

    def test_both_round24_slots_prefer_a_fresh_design(self):
        for fast in (False, True):
            with self.subTest(fast=fast), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                details = root/'gate/cand-round23-1113a/details.csv'
                details.parent.mkdir(parents=True)
                details.write_text('n,score\n2,1.0\n')
                take = root/'take-harvest-r24'
                (take/'work').mkdir(parents=True)
                (take/'work/deadline').write_text(str(int(time.time()+60)))
                packing = root/'packing.csv'
                H.rows_write(packing, [dict(n='2', square_id=str(i), x=repr(.5+i*(1+3e-11)), y='.5', angle='0') for i in range(2)])
                follow = H.Follow(SimpleNamespace(scratch=str(root), take=str(take), round=24,
                                                 base_round=23, base_gate='cand-round23-1113a'))
                follow.state = lambda message: None
                follow.fast = fast
                row = dict(n='2', start='.42', source='control', licence='ours')
                items = [dict(key=letter*64, kind=kind, priority=priority, created=time.time(),
                              queued=time.time(), path=str(packing), row=dict(row))
                         for letter, kind, priority in (('a', 'design', 0), ('b', 'take', 2))]
                follow.pending = {item['key']: item for item in items}
                with patch.object(H.subprocess, 'Popen', return_value=SimpleNamespace(pid=123)):
                    follow.start()
                self.assertEqual(follow.run_item['key'], 'a'*64)
                self.assertEqual(follow.run_item['limit'], 45 if fast else 180)

    def test_public_credit_inside_a_dataset_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root/'ds/owner__data'
            folder.mkdir(parents=True)
            with zipfile.ZipFile(folder/'data.zip', 'w') as zipped:
                zipped.writestr('credits/per_n.csv', 'n,L,src\n639,25.7761109863,notebooks/penguin069/squares-joegun-boxed-certified-union\n')
                zipped.writestr('unused.py', 'raise RuntimeError("data only")')
            row = H.public_origin(root, dict(n='639', L='25.7761109863', source='owner/data :: data.zip!submission.csv', licence='Apache 2.0'))
            self.assertIn('data.zip!credits/per_n.csv', row['source'])
            self.assertIsNotNone(H.refused_source(row, root))

    def test_polished_public_baseline_and_excluded_side(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root/'public/data'
            first = data/'nb/owner__book'
            parent = data/'nb/parent__book'
            first.mkdir(parents=True)
            parent.mkdir(parents=True)
            (first/'per_n_source_table.csv').write_text('n,official_side_L,source_ref\n639,25.7761109863,parent/book\n542,23.8,parent/book\n')
            (parent/'submission_sources.csv').write_text('n,L,source\n639,25.7761109863,sub:submission_merged.csv\n542,23.8,sub:submission_merged.csv\n')
            old = root/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479'
            old.mkdir(parents=True)
            (old/'per_n.csv').write_text('n,L,src\n639,25.7761109863,notebooks/penguin069/squares-joegun-boxed-certified-union\n')
            good = H.public_origin(data, dict(n='542', L='23.7', source='owner/book :: submission.csv', licence='Apache 2.0'))
            self.assertIn('parent/book', good['source'])
            self.assertIn('sub:submission_merged.csv', good['source'])
            self.assertIsNone(H.refused_source(good, root))
            bad = H.public_origin(data, dict(n='639', L='25.7761109863', source='owner/book :: submission.csv', licence='Apache 2.0'))
            self.assertIsNotNone(H.refused_source(bad, root))
            polished = H.public_origin(data, dict(n='639', L='25.77', source='owner/book :: submission.csv', licence='Apache 2.0'))
            self.assertIsNotNone(H.refused_source(polished, root))

    def test_second_public_delta_respects_its_start_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            follow = H.Follow.__new__(H.Follow)
            follow.w = root
            follow.s = root
            follow.public_stage = 'done'
            follow.deadline = time.time()+600
            follow.deadline_label = 'fixture'
            follow.state = lambda message: None
            plan = root/'public-next.json'
            config = dict(previous=str(root/'public/data'), out=str(root/'public2'), not_before=time.time()+300)
            plan.write_text(json.dumps(config))
            fake = SimpleNamespace(pid=123, poll=lambda: None)
            with patch.object(H.subprocess, 'Popen', return_value=fake) as launch:
                follow.public()
                launch.assert_not_called()
                self.assertTrue(plan.exists())
                config['not_before'] = time.time()-1
                plan.write_text(json.dumps(config))
                follow.public()
                launch.assert_called_once()
            self.assertEqual(follow.public_stage, 'fetch')
            self.assertTrue((root/'public-plan-started.json').exists())
            self.assertIn(str(root/'public/data'), (root/'public.sh').read_text())

    def test_nested_excluded_ancestor_and_candidate_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'child.json'
            parent = root / 'parent.json'
            child.write_text(json.dumps(dict(finish_source='take-midm-r23/639.csv', finish_licence='ours')))
            parent.write_text(json.dumps(dict(source='source metadata ' + str(child))))
            row = dict(source='source metadata ' + str(parent), licence='ours')
            self.assertIsNotNone(H.refused_source(row, root))
            child.write_text(json.dumps(dict(source='gather/round23-2026-11-13a.csv n639',
                                            policy=dict(excluded=['take-midm-r23/639.csv']))))
            self.assertIsNone(H.refused_source(row, root))
            details = root / 'gate/cand-round23-1113a/details.csv'
            details.parent.mkdir(parents=True)
            details.write_text('n,score\n639,0.02\n')
            take = root / 'take-harvest-r24'
            (take/'work').mkdir(parents=True)
            (take/'work/deadline').write_text(str(int(time.time()+60)))
            follow = H.Follow(SimpleNamespace(scratch=str(root), take=str(take), round=24,
                                             base_round=23, base_gate='cand-round23-1113a'))
            self.assertEqual(follow.collector.args.live, [str(root/'take-*-r24')])
            self.assertEqual(follow.collector.args.out, [str(take)])
            self.assertEqual(follow.collector.args.remote_dir, 'scratch/squares-harvest/r24')
            self.assertEqual(follow.bars(), {639: 0.02})

    def test_public_credit_must_match_side(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'nb/owner__book'
            folder.mkdir(parents=True)
            (folder / 'per_n.csv').write_text('n,L,src\n639,25.776110986348524,notebooks/penguin069/squares-joegun-boxed-certified-union\n')
            row = dict(n='639', L='25.776110986348524', source='owner/book :: submission.csv', licence='Apache 2.0')
            credited = H.public_origin(root, row)
            self.assertIsNotNone(H.refused_source(credited, root))
            different = H.public_origin(root, dict(row, L='26'))
            self.assertEqual(different['source'], row['source'])
            (folder / 'per_n.csv').unlink()
            self.assertEqual(H.public_origin(root, row), row)

    def test_seen_winner_stages_before_search_but_tie_does_not(self):
        for winner in (True, False):
            with self.subTest(winner=winner), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                details = root / 'gate/cand-round21-1113a/details.csv'
                details.parent.mkdir(parents=True)
                details.write_text('n,score\n2,1.0\n')
                take = root / 'take-harvest-r23'
                (take / 'work').mkdir(parents=True)
                (take / 'work/deadline').write_text(str(int(time.time()+60)))
                packing = root / 'packing.csv'
                rows = [dict(n='2', square_id=str(i), x=repr(.5+i*(1+3e-11)), y='.5', angle='0') for i in range(2)]
                H.rows_write(packing, rows)
                follow = H.Follow(SimpleNamespace(scratch=str(root), take=str(take)))
                follow.state = lambda message: None
                certificate = follow.collector.cert(packing, 2)
                self.assertIsNotNone(certificate)
                follow.current_bars = {2: certificate[0] + (3e-10 if winner else 0)}
                follow.done.add(hashlib.sha256(packing.read_bytes()).hexdigest())
                follow.shapes.add(follow.shape(rows))
                follow.enqueue(packing, dict(source='approved control', licence='ours, control'), 'design')
                staged = H.table(follow.raw / 'take.tsv')
                self.assertEqual(bool(staged), winner)


if __name__ == '__main__':
    unittest.main()
