from abc import ABC, abstractmethod
from app.models.domain_models import ParsedJob, UserProfile, MetricScore

class BaseMetric(ABC):
    """
    Abstract base class for all evaluation metrics.
    """
    def __init__(self, weight: float):
        self.weight = weight

    @abstractmethod
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        pass


class SkillMatchMetric(BaseMetric):
    """Evaluates how many of the job's required skills the user has."""
    
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        if not job.required_skills:
            return MetricScore(metric_name="Skill Match", score=1.0, weight=self.weight, reasoning="No required skills specified.")
            
        profile_skills = {s.lower() for s in profile.core_skills}
        job_skills = {s.lower() for s in job.required_skills}
        
        matched_skills = job_skills.intersection(profile_skills)
        score = len(matched_skills) / len(job_skills)
        
        reasoning = f"Matched {len(matched_skills)}/{len(job_skills)} required skills ({', '.join(matched_skills) if matched_skills else 'None'})."
        
        return MetricScore(
            metric_name="Skill Match", 
            score=score, 
            weight=self.weight, 
            reasoning=reasoning
        )


class ExperienceMetric(BaseMetric):
    """Evaluates if the user meets the minimum experience required."""
    
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        if profile.years_of_experience >= job.minimum_years_experience:
            score = 1.0
            reasoning = f"User has {profile.years_of_experience}y, meets minimum of {job.minimum_years_experience}y."
        else:
            # Penalize linearly, floor at 0
            gap = job.minimum_years_experience - profile.years_of_experience
            score = max(0.0, 1.0 - (gap * 0.2)) # -20% per missing year
            reasoning = f"User is missing {gap} years of experience."
            
        return MetricScore(
            metric_name="Experience Match", 
            score=score, 
            weight=self.weight, 
            reasoning=reasoning
        )


class LocationMetric(BaseMetric):
    """Evaluates if the job's location matches the user's preference."""
    
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        job_loc = job.location_type.lower()
        pref_loc = profile.preferred_location_type.lower()
        
        if pref_loc == "any" or job_loc == pref_loc:
            score = 1.0
            reasoning = "Perfect location match."
        elif pref_loc == "remote" and job_loc == "hybrid":
            score = 0.5
            reasoning = "Wants Remote, job is Hybrid."
        else:
            score = 0.0
            reasoning = f"Wants {pref_loc}, job is {job_loc}."
            
        return MetricScore(
            metric_name="Location Match", 
            score=score, 
            weight=self.weight, 
            reasoning=reasoning
        )
