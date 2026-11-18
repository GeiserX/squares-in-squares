def should_stop(start_score, live_score, held_score):
    return live_score < min(start_score, held_score) - 1e-6


def control():
    cases = [
        ('donor-above-held-live-at-held', .1001, .1, .1, False),
        ('donor-with-lower-live', .1001, .1 - 2e-6, .1, True),
        ('held-with-lower-live', .1, .1 - 2e-6, .1, True),
        ('held-alone', .1, .1, .1, False),
    ]
    results = []
    for name, start, live, held, expected in cases:
        actual = should_stop(start, live, held)
        assert actual == expected, name
        results.append({'case': name, 'stop': actual, 'expected': expected})
    return results


if __name__ == '__main__':
    import json
    from pathlib import Path
    receipt = {'passed': True, 'cases': control()}
    Path(__file__).with_name('stop-control37.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
