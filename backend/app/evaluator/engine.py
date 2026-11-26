from typing import List
from app.models.domain_models import ParsedJob, UserProfile, JobEvaluation
from app.evaluator.metrics import BaseMetric

class JobEvaluator:
    """
    The orchestrator for the evaluation engine.
    It takes a list of injected metrics, runs them all, and aggregates the final score.
    """
    
    def __init__(self, metrics: List[BaseMetric], passing_threshold: float = 75.0):
        self.metrics = metrics
        self.passing_threshold = passing_threshold
        
    def evaluate(self, raw_job_id: str, job: ParsedJob, profile: UserProfile) -> JobEvaluation:
        metric_scores = []
        
        for metric in self.metrics:
            score_result = metric.calculate(job, profile)
            metric_scores.append(score_result)
            
        # Calculate weighted average
        total_weight = sum(m.weight for m in self.metrics)
        if total_weight == 0:
            final_score = 0.0
        else:
            final_score = sum(m.score * m.weight for m in metric_scores) / total_weight
            
        final_percentage = final_score * 100
        
        return JobEvaluation(
            raw_job_id=raw_job_id,
            total_score=final_percentage,
            metrics=metric_scores,
            is_passed=final_percentage >= self.passing_threshold
        )
