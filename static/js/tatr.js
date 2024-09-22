function handleSecondButtonClick(event) {
    // Prevent default form submission behavior (if necessary)
    event.preventDefault();

    // Access the selected file(s)
    const file = event.target.files[0];  // Access the first selected file

    if (file) {
        console.log('File selected:', file.name);

        // Create a new FormData object to hold the file
        const formData = new FormData();
        formData.append('file', file);  // 'file' should match the backend parameter name

        // Send the file to the backend API using fetch
        fetch('/api/tatr', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('File upload failed');
            }
            return response.json();  // Assuming the backend returns JSON
        })
        .then(data => {
            console.log('Upload successful!', data);
            // You can handle the response data here (e.g., show a success message)
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    } else {
        console.log('No file selected');
    }
}
