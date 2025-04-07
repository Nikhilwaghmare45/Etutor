import pandas as pd
import random
import os

def load_assessment_data():
    """Load the assessment data from CSV files"""
    try:
        data_analytics = pd.read_csv('data/data_analytics_new.csv').to_dict(orient='records')
        full_stack = pd.read_csv('data/full_stack_new.csv').to_dict(orient='records')
        python = pd.read_csv('data/python_new.csv').to_dict(orient='records')
        return data_analytics, full_stack, python
    except FileNotFoundError as e:
        # If files are not found, try to load from attached_assets
        try:
            data_analytics = pd.read_csv('attached_assets/data_analytics_new.csv').to_dict(orient='records')
            full_stack = pd.read_csv('attached_assets/full_stack_new.csv').to_dict(orient='records')
            python = pd.read_csv('attached_assets/python_new.csv').to_dict(orient='records')
            return data_analytics, full_stack, python
        except Exception as e:
            print(f"Error loading data: {e}")
            return [], [], []

def generate_mcqs(data, question_type, num_questions=5, course_name=""):
    """Generate MCQs based on the data and question type"""
    mcqs = []
    if not data:
        return mcqs
        
    selected_indices = random.sample(range(len(data)), min(num_questions, len(data)))
    for index in selected_indices:
        item = data[index]
        concept = item["Concept"]
        description = item["Description"]
        
        # Generate options
        options = [description]
        while len(options) < 4:
            random_item = random.choice(data)
            if random_item["Description"] not in options:
                options.append(random_item["Description"])
        
        random.shuffle(options)  # Shuffle options
        
        # Create question based on type
        if question_type == "descriptive":
            question = f"What is {concept}?"
        elif question_type == "application":
            question = f"Which of the following best describes the use of {concept}?"
        elif question_type == "analytical":
            if len(data) > 1:
                other_concept = random.choice([item for item in data if item["Concept"] != concept])
                question = f"What is the main difference between {concept} and {other_concept['Concept']}?"
                options = [
                    f"{concept} is {description}", 
                    f"{other_concept['Concept']} is {other_concept['Description']}"
                ]
                # Add two more random options
                additional_options = []
                while len(additional_options) < 2:
                    random_item = random.choice(data)
                    option_text = f"{random_item['Concept']} is {random_item['Description']}"
                    if option_text not in options and option_text not in additional_options:
                        additional_options.append(option_text)
                
                options.extend(additional_options)
                random.shuffle(options)
                
                # Set the first option (concept is...) as the answer
                answer = f"{concept} is {description}"
            else:
                # Fallback to descriptive if not enough data for analytical
                question = f"What is {concept}?"
                answer = description
        else:
            # Default to descriptive
            question = f"What is {concept}?"
            answer = description
        
        mcqs.append({
            "question": question,
            "options": options,
            "answer": description if question_type != "analytical" or len(data) <= 1 else answer,
            "course": course_name
        })
    
    return mcqs

def generate_assessment_questions(data_analytics, full_stack, python):
    """Generate assessment questions from all three courses"""
    data_analytics_mcqs = generate_mcqs(data_analytics, "descriptive", course_name="Data Analytics")
    full_stack_mcqs = generate_mcqs(full_stack, "application", course_name="Full Stack")
    python_mcqs = generate_mcqs(python, "analytical", course_name="Python")
    
    all_questions = data_analytics_mcqs + full_stack_mcqs + python_mcqs
    random.shuffle(all_questions)  # Shuffle all questions
    
    # Add question IDs
    for i, question in enumerate(all_questions):
        question["id"] = i + 1
    
    return all_questions

def evaluate_assessment(answers, data_analytics, full_stack, python):
    """
    Evaluate the assessment answers and return scores for each course
    including recommended starting chapter
    
    Args:
        answers (dict): User's answers from the assessment form
        data_analytics (pd.DataFrame): Data analytics assessment questions
        full_stack (pd.DataFrame): Full stack assessment questions
        python (pd.DataFrame): Python assessment questions
        
    Returns:
        dict: Dictionary with course scores and recommended starting chapters
    """
    # Initialize scores and recommended chapters
    result = {
        "scores": {
            "Data Analytics": 0,
            "Full Stack": 0,
            "Python": 0
        },
        "recommended_chapters": {
            "python": 1,
            "data_analytics": 1,
            "full_stack": 1
        }
    }
    
    # Generate all questions to get the answers
    all_questions = generate_assessment_questions(data_analytics, full_stack, python)
    
    # Create a mapping of question IDs to their answers and courses
    question_map = {str(q["id"]): {"answer": q["answer"], "course": q["course"]} for q in all_questions}
    
    # Count total questions per course for percentage calculation
    course_question_count = {
        "Data Analytics": 0,
        "Full Stack": 0,
        "Python": 0
    }
    
    for q in all_questions:
        course_question_count[q["course"]] += 1
    
    # Process user answers
    correct_per_course = {
        "Data Analytics": 0,
        "Full Stack": 0,
        "Python": 0
    }
    
    for question_id, answer_index in answers.items():
        if question_id.startswith("question_"):
            q_id = question_id.split("_")[1]
            if q_id in question_map:
                question_info = question_map[q_id]
                selected_answer = all_questions[int(q_id) - 1]["options"][int(answer_index) - 1]
                
                if selected_answer == question_info["answer"]:
                    result["scores"][question_info["course"]] += 1
                    correct_per_course[question_info["course"]] += 1
    
    # Calculate percentage scores for each course
    percentages = {}
    for course, count in course_question_count.items():
        if count > 0:
            percentages[course] = (correct_per_course[course] / count) * 100
        else:
            percentages[course] = 0
    
    # Determine recommended starting chapters based on performance
    result["recommended_chapters"] = recommend_starting_chapters(percentages)
    
    # Return just the scores for backward compatibility
    # In the future, we could return the full result object
    return result["scores"]

def recommend_starting_chapters(score_percentages):
    """
    Recommend starting chapters based on assessment scores using a simple ML-like approach
    """
    recommended_chapters = {
        "python": 1,
        "data_analytics": 1,
        "full_stack": 1
    }
    
    # Define thresholds for chapter recommendations
    # Based on score percentage, recommend starting at different chapters
    thresholds = {
        "beginner": 30,     # 0-30% - start at chapter 1
        "intermediate": 60, # 31-60% - start at chapter 3
        "advanced": 80      # 61-80% - start at chapter 5
                            # 81-100% - start at chapter 7
    }
    
    # Map course names to keys used in the recommended_chapters dict
    course_key_map = {
        "Python": "python",
        "Data Analytics": "data_analytics",
        "Full Stack": "full_stack"
    }
    
    for course, percentage in score_percentages.items():
        course_key = course_key_map.get(course)
        if course_key:
            if percentage <= thresholds["beginner"]:
                # Beginner level - start at chapter 1
                recommended_chapters[course_key] = 1
            elif percentage <= thresholds["intermediate"]:
                # Intermediate level - start at chapter 3
                recommended_chapters[course_key] = 3
            elif percentage <= thresholds["advanced"]:
                # Advanced level - start at chapter 5
                recommended_chapters[course_key] = 5
            else:
                # Expert level - start at chapter 7
                recommended_chapters[course_key] = 7
    
    return recommended_chapters
