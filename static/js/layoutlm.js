async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);  // FastAPI expects 'file' as the key

        // Show loading overlay
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }

        try {
            // Send the file to the server
            const response = await fetch("/api/layout", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("File upload failed");
            }

            const result = await response.json();
            
            // Hide loading overlay
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }

            // Show the uploaded image (input image)
            const uploadedImageElement = document.getElementById('uploadedImage');
            const imageURL = URL.createObjectURL(file);  // Convert uploaded file to a URL
            uploadedImageElement.src = imageURL;
            uploadedImageElement.style.display = 'block';  // Make it visible

            // Get the processed image path from the response and draw on the canvas
            const processedImagePath = result.output_image_path;
            const processedImage = new Image();
            processedImage.src = processedImagePath;

            // Once the processed image loads, draw it on the canvas
            processedImage.onload = function() {
                const canvas = document.getElementById('imageCanvas');
                const ctx = canvas.getContext('2d');
                
                // Set canvas dimensions same as processed image
                canvas.width = processedImage.width;
                canvas.height = processedImage.height;
                canvas.style.display = 'block';  // Make it visible

                // Draw the processed image on the canvas
                ctx.drawImage(processedImage, 0, 0, processedImage.width, processedImage.height);
            };

            // Handle qa_pairs and trigger download
            const qa_pairs = result.qa_pairs;  // Assuming qa_pairs is an array or object

            if (qa_pairs) {
                downloadJson(qa_pairs, 'qa_pairs.json');
            }

        } catch (error) {
            console.error("Error during file upload:", error);
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }
}

// Function to download JSON data
function downloadJson(data, filename) {
    const jsonString = JSON.stringify(data, null, 2);  // Convert to JSON string
    const blob = new Blob([jsonString], { type: 'application/json' });  // Create a blob
    const url = URL.createObjectURL(blob);  // Create a URL for the blob

    const a = document.createElement('a');  // Create a link element
    a.href = url;
    a.download = filename;  // Set the download filename
    document.body.appendChild(a);  // Append to the body
    a.click();  // Programmatically click the link to trigger the download
    document.body.removeChild(a);  // Remove the link from the document
    URL.revokeObjectURL(url);  // Release the blob URL
}
