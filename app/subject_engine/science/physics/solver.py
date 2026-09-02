"""
Physics Master Solver Orchestrator
==================================

PURPOSE:
    Central deterministic Physics solver coordinating numerical extraction,
    specialized calculation engines, and concept knowledge lookup.
"""

import time
from typing import Optional, Any
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import physics_parser
from app.subject_engine.science.physics.concepts import physics_kb
from app.subject_engine.science.physics.engines.mechanics import mechanics_engine
from app.subject_engine.science.physics.engines.work_energy import work_energy_engine
from app.subject_engine.science.physics.engines.electricity import electricity_engine
from app.subject_engine.science.physics.engines.waves_sound import waves_sound_engine
from app.subject_engine.science.physics.engines.optics import optics_engine
from app.subject_engine.science.physics.engines.electronics import electronics_engine


class PhysicsSolver:
    """Master solver orchestrator for Physics."""

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        start_time = time.monotonic()
        raw_q = query.strip()
        lower_q = raw_q.lower()

        # Step 1: Electronics / Logic Gates Check
        elec_res = electronics_engine.solve(raw_q)
        if elec_res:
            return self._finalize(elec_res, start_time, raw_q)

        # Step 2: Parse numerical quantities
        parsed = physics_parser.parse(raw_q)

        # Step 3: Run specialized calculation engines if numerical variables found
        if parsed.variables:
            # Mechanics (F=ma, v=s/t, p=mv)
            mech_res = mechanics_engine.solve(parsed)
            if mech_res:
                return self._finalize(mech_res, start_time, raw_q)

            # Work & Energy (KE, PE, W=Fd, P=W/t)
            we_res = work_energy_engine.solve(parsed)
            if we_res:
                return self._finalize(we_res, start_time, raw_q)

            # Electricity (V=IR, P=VI, R=V/I, I=V/R)
            elec_num_res = electricity_engine.solve(parsed)
            if elec_num_res:
                return self._finalize(elec_num_res, start_time, raw_q)

            # Waves & Sound (v=f*lambda, echo)
            wave_res = waves_sound_engine.solve(parsed)
            if wave_res:
                return self._finalize(wave_res, start_time, raw_q)

            # Optics (P = 1/f)
            opt_res = optics_engine.solve(parsed)
            if opt_res:
                return self._finalize(opt_res, start_time, raw_q)

        # Step 4: Concept Knowledge Base Lookup (definitions, formulas, laws)
        matches = physics_kb.find_by_query(raw_q, threshold=60.0)
        if matches:
            concept, score = matches[0]
            md = science_formatter.format_concept_explanation(
                name=concept.name,
                subject="Physics",
                definition=concept.definition,
                key_points=concept.key_points,
                formula=concept.formula,
                unit=concept.si_unit,
                examples=concept.examples,
                diagram_ascii=concept.diagram_ascii,
            )
            res = SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic=concept.topic,
                concept_id=concept.concept_id,
                intent=QuestionIntent.DEFINE if any(w in lower_q for w in ("what is", "define", "meaning")) else QuestionIntent.EXPLAIN_CONCEPT,
                original_question=raw_q,
                formula=concept.formula,
                rules_applied=concept.key_points,
                steps=[concept.definition],
                answer=concept.formula or concept.definition,
                formatted_markdown=md,
                unit=concept.si_unit,
                confidence=min(0.99, max(0.70, score / 100.0)),
            )
            return self._finalize(res, start_time, raw_q)

        # Unhandled Physics query
        elapsed = (time.monotonic() - start_time) * 1000.0
        return SubjectSolveResult(
            handled_locally=False,
            subject=SubjectType.PHYSICS,
            intent=QuestionIntent.UNKNOWN,
            original_question=raw_q,
            confidence=0.0,
            execution_time_ms=elapsed,
        )

    def _finalize(self, res: SubjectSolveResult, start_time: float, raw_q: str) -> SubjectSolveResult:
        res.execution_time_ms = (time.monotonic() - start_time) * 1000.0
        res.original_question = raw_q
        return res


# Global PhysicsSolver
physics_solver = PhysicsSolver()
