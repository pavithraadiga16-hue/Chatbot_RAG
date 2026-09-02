"""
Matrix & Determinant Engine
===========================

PURPOSE:
    Solves matrix algebra and determinant operations:
    - Matrix Addition, Subtraction, Multiplication
    - Transpose of Matrix
    - Determinants (2x2, 3x3)
    - Adjoint and Matrix Inversion
    - Cramer's Rule for Linear Systems
"""

import ast
import re
from typing import Optional
import sympy as sp
import numpy as np

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.validators import validate_matrix_dimensions


class MatrixEngine:
    """Specialized engine for Matrix and Determinant operations."""

    def parse_matrix(self, text: str) -> Optional[sp.Matrix]:
        """Parses matrix literal like [[1, 2], [3, 4]] or [[1,2,3],[4,5,6]]."""
        mat_match = re.search(r'(\[\[.*?\]\])', text)
        if not mat_match:
            return None

        mat_str = mat_match.group(1)
        try:
            raw_list = ast.literal_eval(mat_str)
            if isinstance(raw_list, list) and all(isinstance(r, list) for r in raw_list):
                rows = len(raw_list)
                cols = len(raw_list[0]) if rows > 0 else 0
                validate_matrix_dimensions(rows, cols)
                return sp.Matrix(raw_list)
        except Exception:
            pass
        return None

    def solve_matrix_operation(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Handles determinant, transpose, inverse, and multiplication of matrices.
        """
        lower_q = query.lower()

        # Find all matrix literals
        mat_matches = re.findall(r'(\[\[.*?\]\])', query)
        matrices = []
        for m_str in mat_matches:
            try:
                raw_list = ast.literal_eval(m_str)
                if isinstance(raw_list, list) and all(isinstance(r, list) for r in raw_list):
                    matrices.append(sp.Matrix(raw_list))
            except Exception:
                pass

        if not matrices:
            return None

        is_det = bool(re.search(r'\b(determinant|det)\b', lower_q))
        is_transpose = bool(re.search(r'\b(transpose)\b', lower_q))
        is_inverse = bool(re.search(r'\b(inverse)\b', lower_q))
        is_multiply = bool(re.search(r'\b(multiply|multiplication|product)\b', lower_q)) or len(matrices) >= 2

        if is_det and len(matrices) >= 1:
            M = matrices[0]
            if M.rows != M.cols:
                return None
            det_val = M.det()
            steps = [
                f"Given Matrix A ({M.rows}×{M.cols}):",
                f"`{M.tolist()}`",
                f"Calculate Determinant |A|:",
            ]
            if M.rows == 2:
                steps.append(f"For 2×2 matrix `[[a, b], [c, d]]`: `det(A) = ad - bc`")
                steps.append(f"`det(A) = ({M[0,0]} × {M[1,1]}) - ({M[0,1]} × {M[1,0]}) = {det_val}`")
            else:
                steps.append(f"Expand along First Row using minors and cofactors:")
                steps.append(f"**|A| = {det_val}**")

            answer = str(det_val)
            title = f"Determinant of {M.rows}×{M.cols} Matrix"
            formula = "det([[a, b], [c, d]]) = ad - bc"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="matrices",
                concept_id="math.matrix",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_transpose and len(matrices) >= 1:
            M = matrices[0]
            T = M.T
            steps = [
                f"Given Matrix A ({M.rows}×{M.cols}): `{M.tolist()}`",
                f"Transpose Aᵀ interchanges rows and columns (Aᵀ[i][j] = A[j][i]).",
                f"**Aᵀ = `{T.tolist()}` ({T.rows}×{T.cols})**",
            ]
            answer = str(T.tolist())
            title = "Transpose of Matrix"
            formula = "Aᵀ[i, j] = A[j, i]"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="matrices",
                concept_id="math.matrix",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_inverse and len(matrices) >= 1:
            M = matrices[0]
            if M.rows != M.cols:
                return None
            det_val = M.det()
            steps = [
                f"Given Square Matrix A ({M.rows}×{M.cols}): `{M.tolist()}`",
                f"Determinant |A| = `{det_val}`",
            ]
            if det_val == 0:
                steps.append(f"Since |A| = 0, Matrix A is singular and has NO inverse.")
                answer = "Matrix is Singular (No inverse exists)"
            else:
                inv = M.inv()
                steps.append(f"Adjoint adj(A) computed from matrix of cofactors.")
                steps.append(f"Formula: `A⁻¹ = (1/|A|) × adj(A)`")
                steps.append(f"**A⁻¹ = `{inv.tolist()}`**")
                answer = str(inv.tolist())

            title = "Matrix Inverse (A⁻¹)"
            formula = "A⁻¹ = (1/det(A)) · adj(A)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="matrices",
                concept_id="math.matrix",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_multiply and len(matrices) >= 2:
            A, B = matrices[0], matrices[1]
            if A.cols != B.rows:
                return None
            C = A * B
            steps = [
                f"Matrix A ({A.rows}×{A.cols}): `{A.tolist()}`",
                f"Matrix B ({B.rows}×{B.cols}): `{B.tolist()}`",
                f"Matrix Multiplication Condition: Number of columns of A ({A.cols}) = Number of rows of B ({B.rows}).",
                f"Compute Row × Column Dot Products for each element:",
                f"**Result C = A × B = `{C.tolist()}` ({C.rows}×{C.cols})**",
            ]
            answer = str(C.tolist())
            title = "Matrix Multiplication (A × B)"
            formula = "C[i, j] = Σ A[i, k] · B[k, j]"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="matrices",
                concept_id="math.matrix",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None


# Global instance
matrix_engine = MatrixEngine()
