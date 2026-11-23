"""Integration tests with synthetic bytes; optional professor reference comparison."""
import argparse
from collections import OrderedDict
from pathlib import Path
import random
import re
import subprocess
import tempfile


def reference(addresses, pages, policy, data):
    resident = OrderedDict()
    tlb = [None] * 16
    lines = []
    faults = hits = 0
    for tick, address in enumerate(addresses, 1):
        page, offset = divmod(address, 256)
        slot = next((i for i, e in enumerate(tlb) if e and e[0] == page), None)
        if slot is not None:
            hits += 1
            frame = tlb[slot][1]
            if policy == 'lru':
                tlb[slot] = (page, frame, tick)
        else:
            if page not in resident:
                faults += 1
                if len(resident) == 128:
                    victim, frame = resident.popitem(last=False)
                    tlb = [None if e and e[0] == victim else e for e in tlb]
                else:
                    frame = len(resident)
                resident[page] = frame
            frame = resident[page]
            slot = next((i for i, e in enumerate(tlb) if e is None), None)
            if slot is None:
                slot = min(range(16), key=lambda i: tlb[i][2])
            tlb[slot] = (page, frame, tick)
        if pages == 'lru':
            resident.move_to_end(page)
        byte = data[address]
        value = byte if byte < 128 else byte - 256
        lines.append(f'Virtual address: {address} TLB: {slot} Physical address: {frame * 256 + offset} Value: {value}')
    count = len(addresses)
    return lines + [f'Number of Translated Addresses = {count}', f'Page Faults = {faults}',
                    f'Page Fault Rate = {faults / count:.3f}', f'TLB Hits = {hits}',
                    f'TLB Hit Rate = {hits / count:.3f}']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--executable', default='./vm')
    parser.add_argument('--addresses', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--backing', type=Path)
    args = parser.parse_args()
    executable = str(Path(args.executable).resolve())
    rng = random.Random(7)
    data = bytes((p * 37 + o * 13) % 256 for p in range(256) for o in range(256))
    cases = {
        'limits_signed_bytes': [0, 127, 128, 255, 256, 65535, 65535],
        'tlb_replacement': [p * 256 for p in range(16)] + [0, 4096, 0, 256],
        'resident_page_tlb_miss': [p * 256 for p in range(17)] + [0, 0],
        'invalidation_and_page_recency': [p * 256 for p in range(128)] + [0, 0, 32768, 0, 256],
        'repeated_replacement': [p * 256 + 255 for p in range(256)] * 2,
        'random': [rng.randrange(65536) for _ in range(1000)],
    }
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        backing = root / 'BACKING_STORE.bin'
        backing.write_bytes(data)
        output = root / 'correct.txt'

        def run(arguments):
            return subprocess.run([executable, *arguments], cwd=root, capture_output=True, text=True, timeout=90)

        for name, addresses in cases.items():
            (root / 'input.txt').write_text('\n'.join(map(str, addresses)))
            for pages in ('fifo', 'lru'):
                for tlb in ('fifo', 'lru'):
                    result = run(['input.txt', pages, tlb])
                    assert result.returncode == 0, result.stderr
                    assert output.read_text().splitlines() == reference(addresses, pages, tlb, data), (name, pages, tlb)
            print(f'PASS {name}: {len(addresses)} addresses, all four policies', flush=True)

        for arguments in ([], ['input.txt'], ['input.txt', 'fifo', 'fifo', 'extra'],
                          ['input.txt', 'bad', 'fifo'], ['input.txt', 'fifo', 'bad'],
                          ['missing.txt', 'fifo', 'fifo']):
            result = run(arguments)
            assert result.returncode != 0 and result.stderr, arguments
        for text in ('', '\n', 'abc', '-1', '65536', '1 2', '0\ninvalid'):
            (root / 'input.txt').write_text(text)
            result = run(['input.txt', 'fifo', 'fifo'])
            assert result.returncode != 0 and result.stderr, text
            assert 'Number of Translated' not in output.read_text()
        (root / 'input.txt').write_text(' 0 \n65535')
        assert run(['input.txt', 'lru', 'lru']).returncode == 0
        (root / 'input.txt').write_text('65535')
        backing.write_bytes(data[:65500])
        assert 'complete page' in run(['input.txt', 'fifo', 'fifo']).stderr
        backing.unlink()
        assert 'Cannot open BACKING' in run(['input.txt', 'fifo', 'fifo']).stderr
        backing.write_bytes(data)
        output.unlink()
        output.mkdir()
        assert 'Cannot open correct.txt' in run(['input.txt', 'fifo', 'fifo']).stderr
        output.rmdir()
        print('PASS argument, input, backing-store and output errors', flush=True)

        if args.addresses and args.reference:
            (root / 'input.txt').write_text(args.addresses.read_text())
            backing.write_bytes(args.backing.read_bytes() if args.backing else bytes(65536))
            result = run(['input.txt', 'lru', 'fifo'])
            assert result.returncode == 0, result.stderr
            expected = args.reference.read_text().splitlines()
            actual = output.read_text().splitlines()
            if not args.backing:
                normalize = lambda lines: [re.sub(r'Value: -?\d+', 'Value: OMITTED', line).strip() for line in lines]
                actual, expected = normalize(actual), normalize(expected)
            assert actual == expected, 'Professor reference differs'
            print('PASS professor reference: ' + ('complete output' if args.backing else 'all mappings, TLB indices and statistics; byte values excluded'), flush=True)
            print('\n'.join(output.read_text().splitlines()[-5:]), flush=True)


if __name__ == '__main__':
    main()
