from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.spectra import Line, Function, DefUse, Loop
from sflkit.analysis.predicate import (
    Branch,
    ScalarPair,
    VariablePredicate,
    ReturnPredicate,
    NonePredicate,
)
from sflkit.analysis.predicate import (
    EmptyStringPredicate,
    EmptyBytesPredicate,
    IsAsciiPredicate,
)
from sflkit.analysis.predicate import (
    ContainsDigitPredicate,
    ContainsSpecialPredicate,
    Condition,
)

analysis_mapping = dict()

"""Spectra"""
analysis_mapping[AnalysisType.LINE] = Line
analysis_mapping[AnalysisType.FUNCTION] = Function
analysis_mapping[AnalysisType.DEF_USE] = DefUse
analysis_mapping[AnalysisType.LOOP] = Loop

"""Predicates"""
analysis_mapping[AnalysisType.BRANCH] = Branch
analysis_mapping[AnalysisType.SCALAR_PAIR] = ScalarPair
analysis_mapping[AnalysisType.VARIABLE] = VariablePredicate
analysis_mapping[AnalysisType.RETURN] = ReturnPredicate
analysis_mapping[AnalysisType.NONE] = NonePredicate
analysis_mapping[AnalysisType.EMPTY_STRING] = EmptyStringPredicate
analysis_mapping[AnalysisType.EMPTY_BYTES] = EmptyBytesPredicate
analysis_mapping[AnalysisType.ASCII_STRING] = IsAsciiPredicate
analysis_mapping[AnalysisType.DIGIT_STRING] = ContainsDigitPredicate
analysis_mapping[AnalysisType.SPECIAL_STRING] = ContainsSpecialPredicate
analysis_mapping[AnalysisType.CONDITION] = Condition

"""
If you want to add new spectra or predicates, please register them here and in sdtools/analysis/analysis_type.py
"""
