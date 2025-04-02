<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="style.css" />
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <script src="script.js" defer></script>
  <title>Price Prediction Dashboard</title>
</head>
<body>
  <h1>Weekly Price Prediction</h1>
  
  <form id="prediction-form">
    <label>Competitor Price: <input type="number" name="Competitor_Price" required /></label>
    <label>Marketing Spend: <input type="number" name="Marketing_Spend" required /></label>
    <label>Economic Index: <input type="number" name="Economic_Index" required /></label>
    <label>Holiday Week (0/1): <input type="number" name="Holiday_Week" required /></label>
    <label>Seasonality Price: <input type="number" name="Seasonality_Price" required /></label>
    <label>Quantity: <input type="number" name="Quantity" required /></label>
    <label>Demand Index: <input type="number" name="Demand_Index" required /></label>
    <label>Discount Percentage: <input type="number" name="Discount_Percentage" required /></label>
    <button type="submit">Predict Price</button>
  </form>
  <h2>Prediction Results</h2>
  <div id="prediction-result"></div>

  <h2>Model Performance</h2>
  <div id="performance-dashboard"></div>

  <script>
    // Handle CSV Upload
    document.getElementById('upload-form').onsubmit = function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files.length) {
        alert('Please select a CSV file');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    axios.post('http://127.0.0.1:5000/predict', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      .then(response => {
        console.log(response.data); // Inspect the response here
        if (Array.isArray(response.data)) {
          let resultHTML = '<table border="1"><tr><th>Predicted Price</th></tr>';
          response.data.forEach(row => {
            resultHTML += `<tr><td>${row.Predicted_Price}</td></tr>`;
          });
          resultHTML += '</table>';
          document.getElementById('prediction-result').innerHTML = resultHTML;
        } else {
          document.getElementById('prediction-result').innerHTML = `<p>Error: Expected array but got ${typeof response.data}</p>`;
        }
      })
      .catch(error => {
        document.getElementById('prediction-result').innerHTML = `<p>Error: ${error.response ? error.response.data.error : error.message}</p>`;
      });
      
    axios.get('http://127.0.0.1:5000/performance')
    .then(response => {
        const metrics = response.data;
        const data = [{
        x: Object.keys(metrics),
        y: Object.values(metrics),
        type: 'bar',
        marker: { color: ['#4CAF50', '#2196F3', '#FFC107'] }
        }];
        const layout = { title: 'Model Performance Metrics' };
        Plotly.newPlot('performance-dashboard', data, layout);
    })
    .catch(error => {
        document.getElementById('performance-dashboard').innerHTML = `<p>Error: ${error.response ? error.response.data.error : error.message}</p>`;
    });
    };
  </script>
</body>
</html>
