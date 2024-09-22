async function handleSecondButtonClick(event) {
    // Get the file selected by the user
    const file = event.target.files[0];
    if (!file) {
        alert('Please select a file.');
        return;
    }

    // Show the loading spinner (you could style this element in your CSS)
    document.getElementById('loadingOverlay').style.display = 'flex';

    // Prepare the file to be sent in the FormData object
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Send the file to the FastAPI backend using fetch
        const response = await fetch('http://localhost:8000/api/tatr', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Error during file upload');
        }

        // Receive the CSV file from the backend as a blob
        const csvBlob = await response.blob();
        const csvUrl = window.URL.createObjectURL(csvBlob);

        // Hide the loading spinner
        loadingOverlay.style.display = 'none';

        // Create a link to download the CSV file
        const downloadLink = document.createElement('a');
        downloadLink.href = csvUrl;
        downloadLink.download = 'output.csv';
        downloadLink.innerHTML = 'Download CSV';
        document.body.appendChild(downloadLink);

        // Optionally trigger the download automatically
        downloadLink.click();
        
        // Remove the link from the DOM after the download is triggered
        document.body.removeChild(downloadLink);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the file.');
        loadingOverlay.style.display = 'none';
    }
}
