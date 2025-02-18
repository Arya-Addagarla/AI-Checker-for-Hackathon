let chart = null;

async function predictCode() {
    const codeSnippet = document.getElementById('codeSnippet').value.trim();
    const predictButton = document.getElementById('predictButton');
    const buttonText = document.getElementById('buttonText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const predictionSection = document.getElementById('predictionSection');
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessage = document.getElementById('errorMessage');

    if (!codeSnippet) {
        showError('Please enter some code to analyze.');
        return;
    }

    // Show loading state
    buttonText.style.display = 'none';
    loadingSpinner.style.display = 'inline-block';
    predictButton.disabled = true;
    errorDisplay.style.display = 'none';

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: codeSnippet })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        // Update prediction display
        document.getElementById('resultText').textContent = data.prediction;
        
        // Update confidence chart
        updateConfidenceChart(data.confidence);
        
        // Update explanation list
        const explanationList = document.getElementById('explanationList');
        explanationList.innerHTML = ''; // Clear existing items
        
        if (data.explanations && data.explanations.length > 0) {
            data.explanations.forEach(explanation => {
                const li = document.createElement('li');
                li.textContent = explanation;
                explanationList.appendChild(li);
            });
        }

        // Show results
        predictionSection.style.display = 'block';
        
    } catch (error) {
        showError('An error occurred while analyzing the code. Please try again.');
        console.error('Error:', error);
    } finally {
        // Reset button state
        buttonText.style.display = 'inline-block';
        loadingSpinner.style.display = 'none';
        predictButton.disabled = false;
    }
}

function updateConfidenceChart(confidence) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (chart) {
        chart.destroy();
    }
    
    // Create new chart
    chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Confidence', 'Uncertainty'],
            datasets: [{
                data: [confidence, 100 - confidence],
                backgroundColor: ['#4CAF50', '#f0f0f0'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Update confidence value
    document.getElementById('confidenceValue').textContent = `${Math.round(confidence)}%`;
}

function showError(message) {
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorDisplay.style.display = 'block';
    document.getElementById('predictionSection').style.display = 'none';
}
