import json
import random
from your_module_name import evaluate_test_result

def load_mcq_data(course_name):
    try:
        # Determine the correct file based on the course name
        if course_name == "python":
            filename = 'data/new_python.json'
        elif course_name == "full_stack":
            filename = 'data/new_full_stack.json'
        elif course_name == "data_analytics":
            filename = 'data/new_data_analytics.json'
        else:
            print(f"Unknown course name: {course_name}")
            return None

        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{filename} not found")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in {filename}")
        return None

def generate_nlp_test(chapter_id, course_name="python"):
    mcq_data = load_mcq_data(course_name)
    chapter_key = f"chapter{chapter_id}"

    # Check if the course and chapter exist in the MCQ data
    if mcq_data is None or course_name not in mcq_data or chapter_key not in mcq_data[course_name]["chapters"]:
        print(f"Warning: No MCQ data for {course_name} {chapter_key}.")
        return []

    # Fetch the questions from the MCQ data
    questions = mcq_data[course_name]["chapters"][chapter_key]["questions"]
    
    # Assign IDs to questions for tracking
    for i, question in enumerate(questions):
        question["id"] = i + 1  # Assign an ID starting from 1
        # Determine the correct answer index
        question["correct_answer"] = question["options"].index(question["correct_option"])

    return questions

def evaluate_test_result(answers, questions):
    score = 0
    correct_answers = 0
    total_questions = len(questions)

    for question in questions:
        if answers.get(str(question["id"])) == question["correct_option"]:
            correct_answers += 1

    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score >= 60  # Assuming 60% is the passing score
    return score, passed

def evaluate_test_result(answers, test_questions):
    if not answers or not test_questions:
        print("No answers or questions provided")
        return 0, False

    total_questions = len(test_questions)
    correct_answers = 0

    # Mapping question ID to correct answer index
    question_map = {str(q["id"]): int(q["correct_answer"]) for q in test_questions}

    print(f"Question Map: {question_map}")
    print(f"Raw User Answers: {answers}")

    for question_id, answer_index in answers.items():
        if question_id.startswith("question_"):
            q_id = question_id.split("_")[1]  # Extract numeric ID
            if q_id in question_map:
                try:
                    user_answer = int(answer_index)  # Convert submitted answer to integer
                    correct_answer = question_map[q_id]
                    print(f"Q{q_id}: User Answer = {user_answer}, Correct Answer = {correct_answer}")
                    
                    if user_answer == correct_answer:
                        correct_answers += 1
                        print(f"Q{q_id}: Correct!")
                    else:
                        print(f"Q{q_id}: Incorrect")
                except ValueError:
                    print(f"Invalid answer format for Q{q_id}: {answer_index}")
            else:
                print(f"Question ID {q_id} not found in question map")

    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score_percentage >= 60

    print(f"Score: {correct_answers}/{total_questions} = {score_percentage}%")
    return score_percentage, passed