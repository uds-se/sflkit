from sflkit.analysis import spectra

similarity_coefficients = [
    "AMPLE",
    "AMPLE2",
    "Anderberg",
    "ArithmeticMean",
    "Binary",
    "CBIInc",
    "Cohen",
    "Crosstab",
    "Dice",
    "DStar",
    "Euclid",
    "Fleiss",
    "GP02",
    "GP03",
    "GP13",
    "GP19",
    "Goodman",
    "Hamann",
    "HammingEtc",
    "HarmonicMean",
    "Jaccard",
    "Kulczynski1",
    "Kulczynski2",
    "M1",
    "M2",
    "Naish1",
    "Naish2",
    "Ochiai",
    "Ochiai2",
    "PairScoring",
    "qe",
    "RogersAndTanimoto",
    "Rogot1",
    "Rogot2",
    "RusselAndRao",
    "Scott",
    "SimpleMatching",
    "Sokal",
    "SorensenDice",
    "Tarantula",
    "Wong1",
    "Wong2",
    "Wong3",
    "Zoltar",
]


def _get_similarity_coefficients(similarity_coefficient):
    return lambda po, pn, fo, fn: getattr(
        spectra.Spectrum("", 0, po, pn, fo, fn), similarity_coefficient
    )()


for sc in similarity_coefficients:
    locals()[sc] = _get_similarity_coefficients(sc)

if "sc" in locals():
    del locals()["sc"]
