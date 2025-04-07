document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts for progress visualization
    initializeProgressCharts();
    
    // Set up course selection
    setupCourseSelection();
});

function initializeProgressCharts() {
    // Get the canvas element
    const ctx = document.getElementById('progressChart');
    
    if (!ctx) return;
    
    // Fetch progress data from API
    fetch('/api/progress')
        .then(response => response.json())
        .then(data => {
            // Prepare data for the chart
            const courses = Object.keys(data);
            const percentages = courses.map(course => data[course].percentage);
            const colors = [
                'rgba(75, 192, 192, 0.7)',  // Teal for Python
                'rgba(54, 162, 235, 0.7)',  // Blue for Data Analytics
                'rgba(255, 99, 132, 0.7)'   // Red for Full Stack
            ];
            
            // Create the chart
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: courses.map(course => course.replace('_', ' ').toUpperCase()),
                    datasets: [{
                        label: 'Course Progress (%)',
                        data: percentages,
                        backgroundColor: colors,
                        borderColor: colors.map(color => color.replace('0.7', '1')),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const courseKey = courses[context.dataIndex];
                                    const courseData = data[courseKey];
                                    return [
                                        `Progress: ${courseData.percentage.toFixed(1)}%`,
                                        `Chapter: ${courseData.current_chapter}/9`,
                                        `Status: ${courseData.completed ? 'Completed' : 'In Progress'}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching progress data:', error));
}

function setupCourseSelection() {
    // Add click event to course cards
    const courseCards = document.querySelectorAll('.course-card');
    courseCards.forEach(card => {
        card.addEventListener('click', function() {
            const courseName = this.getAttribute('data-course');
            window.location.href = `/course/${courseName}`;
        });
    });
}
