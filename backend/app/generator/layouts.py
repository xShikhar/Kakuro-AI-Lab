"""Connected short-run layouts and a generated low-entropy fill for bounded recovery."""


def transformed_ribbon(size, rng, extreme=False):
    """Build overlapping 2x2 blocks spanning the grid, then randomize orientation and digits.

    The diagonal band has runs of length two or three. Every block overlaps its
    neighbor, so cells stay connected and none belongs to a singleton run. The
    optional extremal palette creates restrictive clue sums; it is an algorithmic
    witness, not a stored solution. The caller must still count solutions.
    """
    rotations=rng.randrange(4)
    reflect=rng.choice((False,True))
    high=rng.choice((False,True)) if extreme else False
    reverse=rng.choice((False,True)) if extreme else False
    fill={}
    for row in range(1,size):
        for col in range(max(1,row-1),min(size,row+2)):
            # Three colors give distinct digits in every length-three run.
            color=((col-row) if reverse else (row-col))%3
            value=1+color
            if high:
                value=10-value
            rr,cc=row,col
            if reflect:
                cc=size-cc
            for _ in range(rotations):
                rr,cc=cc,size-rr
            fill[f'{rr},{cc}']=value
    return fill
