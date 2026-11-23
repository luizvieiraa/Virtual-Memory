"""Build the Classroom archive with only the required C source and Makefile."""
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parents[1]
target = root / 'lhcv.tar'
with tarfile.open(target, 'w', format=tarfile.USTAR_FORMAT) as archive:
    for name in ('vm.c', 'Makefile'):
        archive.add(root / name, arcname=f'lhcv/{name}')
with tarfile.open(target) as archive:
    assert archive.getnames() == ['lhcv/vm.c', 'lhcv/Makefile']
print(f'Created {target.name}: lhcv/vm.c, lhcv/Makefile')
