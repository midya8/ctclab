"""Original supplied controls, selected in development, not benchmarks."""
from copy import deepcopy


def definitions():
    def item(name,note,frames,width=1,blank=0,symbols=None):
        return dict(name=name,note=note,request=dict(symbols=symbols or ['_','A','B'],blank=blank,frames=frames,beam_width=width))
    wider=[['2/19','9/19','8/19'],['7/17','5/17','5/17'],['2/5','2/5','1/5'],['1/5','3/10','1/2'],['5/14','1/14','4/7']]
    return deepcopy([
        item('A path is not a transcript','Two uniform frames. Lowest-index path ties choose blank, but three paths collapse to A. Width one drops A immediately.',[['1/2','1/2']]*2,symbols=['_','A']),
        item('Keep both prefixes','Same two frames, width two. All mass survives; A has exact mass 3/4.',[['1/2','1/2']]*2,2,symbols=['_','A']),
        item('A blank separates a repeat','A, blank, A must collapse to AA, not A. Zero-probability edges are absent.',[['0','1','0'],['1','0','0'],['0','1','0']]),
        item('The run continues','Six deterministic A frames are one A. Repeating without blank never extends the transcript.',[['0','1','0']]*6),
        item('Blank is not index zero','Here A is the blank label at index one; two zero-index symbols separated by it remain two symbols.',[['1','0','0'],['0','1','0'],['1','0','0']],blank=1),
        item('No frames, one empty path','Empty input has one empty path and transcript, mass one. No fabricated nonempty output.',[]),
        item('A wider beam can lose: width three','Original searched five-frame development control. Width three returns the true MAP AB; it does not retain all of its mass.',wider,3),
        item('A wider beam can lose: width four','Same supplied law, width four. Different pruning yields BAB with smaller true mass. Finite widths are not nested path sets.',wider,4),
        item('Same law without pruning','Same five frames, width 64. Every positive prefix survives, restoring exact transcript masses.',wider,64),
        item('Correct is not certified','Width one finds the true MAP, but lost mass is too large for the sufficient bound. Failure of the bound is not failure of the answer.',[['1/11','2/11','8/11'],['2/5','2/5','1/5'],['1/4','9/20','3/10'],['1/5','1/5','3/5'],['2/7','3/7','2/7']],1),
        item('A strict sufficient margin','A single dominant frame gives a positive strict margin over every alternative plus all discarded mass.',[['1/10','4/5','1/10']],1),
        item('Ties do not become unique','Equal A/B mass chooses lexicographic A, but a strict unique-MAP certificate must remain false.',[['0','1/2','1/2']],1),
    ])
