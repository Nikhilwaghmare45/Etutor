
import numpy as np
from assessment import recommend_starting_chapters

def evaluate_assessment_with_ml(scores):
    """
    Enhanced ML-based evaluation for the user assessment
    Now returns a dictionary of recommended starting chapters for each course
    
    Args:
        scores (dict): Dictionary with course scores from the assessment
        
    Returns:
        dict: Dictionary with recommended starting chapter for each course
    """
    # Calculate percentages for each course (assuming 5 questions per course)
    percentages = {
        "Python": (scores['Python'] / 5) * 100,
        "Data Analytics": (scores['Data Analytics'] / 5) * 100,
        "Full Stack": (scores['Full Stack'] / 5) * 100
    }
    
    # Use the recommend_starting_chapters function from assessment.py
    # to determine the starting chapters for each course
    recommended_chapters = recommend_starting_chapters(percentages)
    
    return recommended_chapters
