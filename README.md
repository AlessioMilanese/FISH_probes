16S FISH probes
========

This tool identify FISH probes from 16S sequences.
Given a clade, it identifies sequences (of a given length) that belong to that and only that clade.

Pre-requisites
--------------

The tool requires:
* Python 3 (or higher)


Installation
--------------

First clone the repo:
```
git clone https://github.com/AlessioMilanese/FISH_probes.git
```

Setup:
```
cd FISH_probes
python setup.py bdist_wheel
pip install --no-deps --force-reinstall dist/*.whl
```

You will need a fasta file with 16S sequences and relative taxonomy.

Simple examples
--------------

Test the design pipeline:
```
fish_probes design -s test/seq.fa -t test/tax -c Firmicutes -k 7
```

It will use the sequences in `test/seq.fa` (taxonomy in `test/tax`) to identify probes of length `7` that are unique for `Firmicutes`.

Find the properties of a specific probe:
```
fish_probes test_probe -i "AATGCATCGATC"
```

It will identify GC content, sequence entropy and melting temperature of the probe `AATGCATCGATC`.
