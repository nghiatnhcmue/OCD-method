==========================================
Gold standards for benchmarking ClusterONE
==========================================

This archive contains the following files the set of reference complexes from
MIPS and SGD that we used to benchmark ClusterONE against alternative
protein complex detection methods.

Each gold standard is contained in a single file in the ``gold_standard``
folder.  These files are in a simple tabular format where each row lists the
members of a particular complex. Columns are separated by whitespace.

The gold standards are as follows:

``mips_3_100``
	This file contains every MIPS ComplexCat category with at least 3 and at
	most 100 members. We have also decided to discard MIPS category 550 as it
	contains non-curated protein complexes that were defined by computerized
	algorithms only; including these would have biased the benchmarks towards
	algorithms that were used to derive the complexes in MIPS category 550.
	MIPS category codes are used as complex IDs. The original MIPS datafile
	was dated 18 May 2006.

``sgd``
	This file contains a gold standard dataset extracted from Gene Ontology
	annotations downloaded from the Saccharomyces Genome Database (SGD).
	The protein complexes in this gold standard were derived from proteins
	annotated by descendant terms of the Gene Ontology term
	*protein complex* (``GO:0043234``). Annotations with modifiers
	such as ``NOT`` or ``colocalizes_with`` and annotations
	supported by ``IEA`` evidence code only were ignored. The original
	annotation files we worked from were downloaded on 11 Aug 2010.
