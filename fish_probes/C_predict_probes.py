import sys
from fish_probes import UTIL_log, UTIL_probe, UTIL_general

VERBOSE = 1

# ------------------------------------------------------------------------------
# Find sequences from the selected clade
# ------------------------------------------------------------------------------
def split_sequences(taxonomy,sel_clade,sequences):
    seq_sel_clade = dict()
    seq_other = dict()
    for seq in taxonomy:
        # we check if any of the selected clades is present
        to_be_added = False
        for s_c in sel_clade:
            if s_c in taxonomy[seq].split(";"):
                to_be_added = True

        # we add it to the correct
        if to_be_added :
            seq_sel_clade[seq] = sequences[seq]
        else:
            seq_other[seq] = sequences[seq]

    if VERBOSE > 2:
        UTIL_log.print_message("Sequences belonging to the selected clade: "+str(len(seq_sel_clade))+".")
        UTIL_log.print_message("Sequences belonging to other clades: "+str(len(seq_other))+".\n")
    return seq_sel_clade, seq_other

# ------------------------------------------------------------------------------
# Find conserved regions in the sequences from the selected clade
# ------------------------------------------------------------------------------
def DnaCheck(sequence):
    return all(base.upper() in ('A', 'C', 'T', 'G', 'U') for base in sequence)

def find_kmers(string,k):
    res = {}
    res_N = {}
    for x in range(len(string)+1-k):
        kmer = string[x:x+k]
        # we select only if they contain nucleotide sequences
        if DnaCheck(kmer):
            res[kmer] = res.get(kmer, 0) + 1
        else:
            res_N[kmer] = res_N.get(kmer, 0) + 1
    return res, res_N

def find_conserved_regions(seq_sel_clade,k,perc_seq_with_kmer):
    all_strings_kmers = dict()
    for s in seq_sel_clade:
        allK,allK_N = find_kmers(seq_sel_clade[s],k)
        all_strings_kmers[s] = allK
    # find all possible k-mers
    all_kmers = set()
    for s in all_strings_kmers:
        for kmer in all_strings_kmers[s]:
            all_kmers.add(kmer)

    if VERBOSE > 2:
        UTIL_log.print_message("Identifed "+str(len(all_kmers))+" unique "+str(k)+"-mers.")
    # now we count how many times it appear
    count_mers = dict()
    for kmer in list(all_kmers):
        count_mers[kmer] = 0
    # now we add the counts per k-mer
    for s in all_strings_kmers:
        for kmer in all_strings_kmers[s]:
            count_mers[kmer] = count_mers[kmer] + 1
    # we check which k-mers covers all sequences
    n_seq = len(seq_sel_clade)
    kmers_recall = dict() # this will be filled in by "check_uniqueness"
    kmers_precision = dict()
    list_identical = list()
    for kmer in count_mers:
        if count_mers[kmer] == n_seq:
            list_identical.append(kmer) # used only to print
        if count_mers[kmer] > n_seq*perc_seq_with_kmer:
            kmers_recall[kmer] = count_mers[kmer]
            kmers_precision[kmer] = 0

    if VERBOSE > 2:
        UTIL_log.print_message("  (Identifed "+str(len(list_identical))+" "+str(k)+"-mers present in all sequences)")
        UTIL_log.print_message(str(len(kmers_precision))+" "+str(k)+"-mers will go to the next step.")
        UTIL_log.print_message("(only k-mers present in at least "+str(perc_seq_with_kmer*100)+"% of the sequences will be used).\n")

    if len(kmers_precision) == 0:
        if VERBOSE > 1:
            UTIL_log.print_warning("No k-mers passed the filter. Please decrease the threshold in -p")
    # return
    return kmers_recall,kmers_precision

def get_kmer_sens(seq_sel_clade, kmer):

    if VERBOSE > 2:
        #UTIL_log.print_message("Identifed "+str(len(all_kmers))+" unique "+str(k)+"-mers.")
        UTIL_log.print_message("Calculating sensitivity for k-mer {}".format(kmer))

    count_mers = sum([True if kmer in seq else False for _, seq in seq_sel_clade.items()])
    
    kmers_recall = dict() # this will be filled in by "check_uniqueness"
    kmers_precision = dict()
    
    kmers_recall[kmer] = count_mers
    kmers_precision[kmer] = 0

    return kmers_recall, kmers_precision

# ------------------------------------------------------------------------------
# Starting from the conserved regions, check if they are unique
# ------------------------------------------------------------------------------
def check_uniqueness(kmers_precision, seq_other, probe_len):
    n_matching_to_other = 0
    # we check if the kmers are covered by other sequences
    other_sel_clades = dict()
    for s in seq_other:
        this_kmers,this_kmers_N = find_kmers(seq_other[s],probe_len)
        for kmer in this_kmers:
            if kmer in kmers_precision:
                kmers_precision[kmer] = kmers_precision[kmer] + 1
                if not kmer in other_sel_clades:
                    other_sel_clades[kmer] = list()
                other_sel_clades[kmer].append(s)
                n_matching_to_other = n_matching_to_other + 1
        # we need to evaluate the ones with an N or others
        for kmer in this_kmers_N:
            dummy = "TODO"

    if VERBOSE > 2:
        UTIL_log.print_message("The selected probes map to other "+str(n_matching_to_other)+" sequences.\n")
    return other_sel_clades

def check_uniqueness_fast(kmers_precision, seq_other, probe_len):
    n_matching_to_other = 0
    # we check if the kmers are covered by other sequences
    other_sel_clades = dict()
    if len(kmers_precision) != 1:
        asddassda
    # is only on...
    for kmer in kmers_precision.keys():
        for s, seq in seq_other.items():
            if kmer in seq:
                kmers_precision[kmer] += 1
                other_sel_clades.setdefault(kmer, []).append(s)
    return other_sel_clades


# ------------------------------------------------------------------------------
# Order to show the probes
# ------------------------------------------------------------------------------
def priotitize_probes(kmers_recall,kmers_precision,n_seq_clade):
    if VERBOSE > 2:
        UTIL_log.print_message("We order the probes by the number of wrong clades.")

    # find the order
    probe_order = list()
    missing = list()
    # best one: cover all sequences, and not in the other clade
    for p in list(kmers_recall.keys()):
        if kmers_recall[p]/n_seq_clade == 1:
            if kmers_precision[p] == 0:
                probe_order.append(p)
            else:
                missing.append(p)
        else:
            missing.append(p)

    if VERBOSE > 2:
        UTIL_log.print_message(str(len(probe_order))+" probe(s) present in all the selected clade(s) and have no contamination.\n")
    probe_order.extend(missing)

    return probe_order


# ------------------------------------------------------------------------------
# Save/Print result
# ------------------------------------------------------------------------------
def save_result(probe_order, outfile, n_seq_clade, kmers_recall,kmers_precision):
    # prepare lines to print
    to_print = list()
    to_print.append("probe\tperc_covered_sequences\tn_covered_sequences\tn_covered_others\tGC_content\tsequence_entropy\tmelting_temperature\tprobe_accessibility\n")

    for kmer in probe_order:
        this_str = kmer+"\t"+str(kmers_recall[kmer]/n_seq_clade)+"\t"
        this_str = this_str+str(kmers_recall[kmer])+"\t"
        this_str = this_str+str(kmers_precision[kmer])+"\t"
        this_str = this_str+UTIL_probe.create_to_print(kmer)
        to_print.append(this_str+"\n")

    UTIL_general.save_file(to_print,outfile)

# ------------------------------------------------------------------------------
# Main function
# ------------------------------------------------------------------------------
# Input:
#  - sequences, dictionary of seq_id -> nucleotide sequence
#  - taxonomy, dictionary of seq_id -> "clade1;clade2;clade3"
#  - sel_clade, clade for which we have to design the probe
#  - probe_len, length for the selected probe (positive integer)
#  - verbose,
#  - outfile, where to save the output. If None, then stdout
def predict_probes(sequences,taxonomy,args):
    # set verbose
    global VERBOSE
    VERBOSE = args.verbose

    # Zero, find sequences that belong to the selected clade
    if VERBOSE > 2:
        UTIL_log.print_log("Identify sequences from the selected clade")
    seq_sel_clade, seq_other = split_sequences(taxonomy,args.sel_clade,sequences)

    # First, identify possible conserved regions
    if VERBOSE > 2:
        UTIL_log.print_log("Identify k-mers for the query clade")
    kmers_recall,kmers_precision = find_conserved_regions(seq_sel_clade,args.probe_len,args.perc_seq)

    # Second, check if identified regions are unique, compared to the other
    # clades (~ evaluating precision)
    if VERBOSE > 2:
        UTIL_log.print_log("Check if the identified k-mers are present in the other clades")
    other_sel_clades = check_uniqueness(kmers_precision,seq_other,args.probe_len)

    # Third, prioritize selected probes
    if VERBOSE > 2:
        UTIL_log.print_log("Prioritize selected probes")
    probe_order = priotitize_probes(kmers_recall,kmers_precision,len(seq_sel_clade))

    # print/save to outfile
    if VERBOSE > 2:
        UTIL_log.print_log("Save the result")
    save_result(probe_order, args.outfile,len(seq_sel_clade),kmers_recall,kmers_precision)


# Main function (2)
# ------------------------------------------------------------------------------
# Input:
#  - sequences, dictionary of seq_id -> nucleotide sequence
#  - taxonomy, dictionary of seq_id -> "clade1;clade2;clade3"
#  - sel_clade, clade for which we have to design the probe
#  - probe_to_evaluate, specific probe to evaluate sensitivity and specificity for
#  - verbose,
#  - outfile, where to save the output. If None, then stdout
def evaluate_probe_sens_spec(sequences,taxonomy,args):
    # set verbose
    global VERBOSE
    VERBOSE = args.verbose

    # Zero, find sequences that belong to the selected clade
    if VERBOSE > 2:
        UTIL_log.print_log("Identify sequences from the selected clade")
    seq_sel_clade, seq_other = split_sequences(taxonomy, args.sel_clade, sequences)

    # First, get k_mer recall of specific probe
    if VERBOSE > 2:
        UTIL_log.print_log("Identifying k-mer recall and precision for the given k-mer")
    kmers_recall, kmers_precision = get_kmer_sens(seq_sel_clade, args.probe_to_evaluate)

    if VERBOSE > 2:
        UTIL_log.print_log("Check if the identified k-mers are present in the other clades")
    other_sel_clades = check_uniqueness_fast(kmers_precision,seq_other, len(args.probe_to_evaluate))
    #print(kmers_sensitivity, kmers_precision)
    #print(other_sel_clades)
    probe_order = priotitize_probes(kmers_recall, kmers_precision,len(seq_sel_clade))

    save_result(probe_order, args.outfile, len(seq_sel_clade), kmers_recall, kmers_precision)